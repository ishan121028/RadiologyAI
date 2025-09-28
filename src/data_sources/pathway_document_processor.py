import pathway as pw
from pathlib import Path
from typing import Dict, List, Optional
import json
import asyncio
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class DocumentSchema(pw.Schema):
    filename: str
    filepath: str
    content: bytes
    file_hash: str
    timestamp: str
    processing_status: str


class ParsedReportSchema(pw.Schema):
    filename: str
    patient_id: str
    study_date: str
    study_type: str
    findings: str
    impression: str
    critical_findings: list
    alert_level: str
    processing_timestamp: str
    parsing_time: float


class CriticalAlertSchema(pw.Schema):
    alert_id: str
    filename: str
    patient_id: str
    alert_level: str
    critical_conditions: list
    findings_summary: str
    recommended_actions: list
    estimated_treatment_time: int
    timestamp: str
    requires_immediate_action: bool


class PathwayDocumentProcessor:
    """Pathway-based real-time document processing pipeline"""
    
    def __init__(self, landingai_api_key: str):
        self.landingai_api_key = landingai_api_key
        self.critical_conditions_db = self._load_critical_conditions()
        
    def _load_critical_conditions(self) -> Dict:
        """Load critical medical conditions database"""
        return {
            "red_alert_conditions": [
                "pulmonary embolism", "aortic dissection", "hemorrhage", "intracranial bleed",
                "tension pneumothorax", "bowel obstruction", "aortic aneurysm rupture",
                "acute stroke", "myocardial infarction", "cardiac tamponade",
                "subdural hematoma", "epidural hematoma", "pneumoperitoneum"
            ],
            "orange_alert_conditions": [
                "pneumonia", "fracture", "mass", "pneumothorax", "appendicitis",
                "kidney stones", "gallbladder inflammation", "abscess", "blood clot",
                "pleural effusion", "consolidation", "nodule"
            ],
            "yellow_alert_conditions": [
                "cyst", "inflammation", "chronic changes", "arthritis",
                "minor fracture", "sinus infection", "muscle strain", "edema"
            ]
        }
    
    def create_document_processing_pipeline(self, file_stream: pw.Table) -> pw.Table:
        """Create the main document processing pipeline using Pathway"""
        
        # Step 1: Parse documents with LandingAI
        parsed_documents = file_stream.select(
            *pw.this,
            parsed_data=parse_radiology_report_with_landingai(
                pw.this.content,
                pw.this.filename,
                self.landingai_api_key
            )
        )
        
        # Step 2: Extract and validate parsing results
        validated_parsing = parsed_documents.select(
            *pw.this,
            parsing_successful=pw.this.parsed_data["success"],
            extracted_findings=pw.this.parsed_data["findings"] if pw.this.parsed_data["success"] else "",
            extracted_impression=pw.this.parsed_data["impression"] if pw.this.parsed_data["success"] else "",
            patient_id=pw.this.parsed_data["patient_id"] if pw.this.parsed_data["success"] else "",
            study_type=pw.this.parsed_data["study_type"] if pw.this.parsed_data["success"] else ""
        ).filter(pw.this.parsing_successful == True)
        
        # Step 3: Detect critical findings
        critical_analysis = validated_parsing.select(
            *pw.this,
            critical_analysis_result=detect_critical_findings(
                pw.this.extracted_findings,
                pw.this.extracted_impression,
                json.dumps(self.critical_conditions_db)
            )
        )
        
        # Step 4: Generate alerts for critical findings
        alert_pipeline = critical_analysis.select(
            *pw.this,
            alert_level=pw.this.critical_analysis_result["alert_level"],
            critical_conditions=pw.this.critical_analysis_result["critical_conditions"],
            requires_alert=pw.this.critical_analysis_result["alert_level"].isin(["RED", "ORANGE"])
        )
        
        # Step 5: Create structured alert objects for critical cases
        critical_alerts = alert_pipeline.filter(
            pw.this.requires_alert == True
        ).select(
            alert_id=generate_alert_id(),
            filename=pw.this.filename,
            patient_id=pw.this.patient_id,
            alert_level=pw.this.alert_level,
            critical_conditions=pw.this.critical_conditions,
            findings_summary=create_findings_summary(
                pw.this.critical_conditions,
                pw.this.alert_level
            ),
            recommended_actions=get_treatment_recommendations(
                pw.this.critical_conditions
            ),
            estimated_treatment_time=estimate_treatment_urgency(
                pw.this.alert_level
            ),
            timestamp=pw.now(),
            requires_immediate_action=pw.this.alert_level == "RED"
        )
        
        return critical_alerts
    
    def create_processing_statistics_pipeline(self, processed_docs: pw.Table) -> pw.Table:
        """Create real-time processing statistics pipeline"""
        
        # Real-time processing metrics
        processing_stats = processed_docs.groupby().reduce(
            total_documents_processed=pw.reducers.count(),
            critical_alerts_red=pw.reducers.sum(
                pw.if_else(pw.this.alert_level == "RED", 1, 0)
            ),
            critical_alerts_orange=pw.reducers.sum(
                pw.if_else(pw.this.alert_level == "ORANGE", 1, 0)
            ),
            avg_processing_time=pw.reducers.avg(pw.this.parsing_time),
            latest_processed=pw.reducers.latest(pw.this.timestamp),
            processing_rate_per_hour=calculate_hourly_processing_rate()
        )
        
        return processing_stats


# Pathway UDFs for document processing

@pw.udf
def parse_radiology_report_with_landingai(content: bytes, filename: str, api_key: str) -> dict:
    """UDF to parse radiology report using LandingAI"""
    
    result = {
        "success": False,
        "patient_id": "",
        "study_date": "",
        "study_type": "",
        "findings": "",
        "impression": "",
        "clinical_history": "",
        "technique": "",
        "error_message": ""
    }
    
    try:
        # Save content to temporary file for LandingAI processing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Simulate LandingAI API call (replace with actual implementation)
            # from landingai import LandingAI
            # client = LandingAI(api_key=api_key)
            # extraction_result = await client.extract_structured_data(...)
            
            # For now, simulate parsing with text extraction
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            extracted_text = ""
            
            for page in pdf_reader.pages:
                extracted_text += page.extract_text()
            
            # Basic pattern matching for demo (replace with LandingAI extraction)
            result.update(extract_medical_data_from_text(extracted_text, filename))
            result["success"] = True
            
            logger.info(f"Successfully parsed {filename}")
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        result["error_message"] = str(e)
        logger.error(f"Error parsing {filename}: {e}")
    
    return result


@pw.udf  
def extract_medical_data_from_text(text: str, filename: str) -> dict:
    """UDF to extract medical data from text (simplified version)"""
    
    import re
    
    data = {
        "patient_id": "",
        "study_date": "",
        "study_type": "",
        "findings": "",
        "impression": "",
        "clinical_history": "",
        "technique": ""
    }
    
    try:
        # Extract patient ID patterns
        patient_id_patterns = [
            r"Patient ID[:\s]+(\w+)",
            r"MRN[:\s]+(\w+)",
            r"Medical Record[:\s]+(\w+)"
        ]
        
        for pattern in patient_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["patient_id"] = match.group(1)
                break
        
        # Extract study date
        date_pattern = r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})"
        date_match = re.search(date_pattern, text)
        if date_match:
            data["study_date"] = date_match.group(1)
        
        # Extract study type
        study_patterns = [
            r"(CT|MRI|X-RAY|ULTRASOUND|PET|MAMMOGRAPHY)",
            r"(Computed Tomography|Magnetic Resonance|Radiograph)"
        ]
        
        for pattern in study_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["study_type"] = match.group(1)
                break
        
        # Extract findings section
        findings_match = re.search(r"FINDINGS?[:\s]+(.*?)(?=IMPRESSION|CONCLUSION|$)", 
                                 text, re.IGNORECASE | re.DOTALL)
        if findings_match:
            data["findings"] = findings_match.group(1).strip()
        
        # Extract impression section
        impression_match = re.search(r"IMPRESSION[:\s]+(.*?)(?=RECOMMENDATION|$)", 
                                   text, re.IGNORECASE | re.DOTALL)
        if impression_match:
            data["impression"] = impression_match.group(1).strip()
        
        # If no patient ID found, generate one from filename
        if not data["patient_id"]:
            data["patient_id"] = f"UNKNOWN_{filename.split('.')[0]}"
            
    except Exception as e:
        logger.error(f"Error extracting medical data: {e}")
    
    return data


@pw.udf
def detect_critical_findings(findings: str, impression: str, conditions_json: str) -> dict:
    """UDF to detect critical findings in radiology reports"""
    
    result = {
        "alert_level": "GREEN",
        "critical_conditions": [],
        "severity_score": 0,
        "confidence": 0.0
    }
    
    try:
        import json
        conditions_db = json.loads(conditions_json)
        
        # Combine findings and impression for analysis
        combined_text = f"{findings} {impression}".lower()
        
        # Check for RED alert conditions (life-threatening)
        for condition in conditions_db["red_alert_conditions"]:
            if condition.lower() in combined_text:
                result["alert_level"] = "RED"
                result["critical_conditions"].append(condition)
                result["severity_score"] = 10
        
        # Check for ORANGE alert conditions (urgent) if not RED
        if result["alert_level"] != "RED":
            for condition in conditions_db["orange_alert_conditions"]:
                if condition.lower() in combined_text:
                    result["alert_level"] = "ORANGE"
                    result["critical_conditions"].append(condition)
                    result["severity_score"] = 6
        
        # Check for YELLOW alert conditions (follow-up) if not RED/ORANGE
        if result["alert_level"] not in ["RED", "ORANGE"]:
            for condition in conditions_db["yellow_alert_conditions"]:
                if condition.lower() in combined_text:
                    result["alert_level"] = "YELLOW"
                    result["critical_conditions"].append(condition)
                    result["severity_score"] = 3
        
        # Calculate confidence based on number of matching conditions
        if result["critical_conditions"]:
            result["confidence"] = min(len(result["critical_conditions"]) * 0.3, 1.0)
        
        if result["alert_level"] != "GREEN":
            logger.info(f"Critical finding detected: {result['alert_level']} - {result['critical_conditions']}")
            
    except Exception as e:
        logger.error(f"Error detecting critical findings: {e}")
    
    return result


@pw.udf
def generate_alert_id() -> str:
    """UDF to generate unique alert ID"""
    import uuid
    return f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"


@pw.udf
def create_findings_summary(conditions: list, alert_level: str) -> str:
    """UDF to create concise findings summary for physicians"""
    
    if not conditions:
        return "No critical findings detected"
    
    conditions_str = ", ".join(conditions)
    
    if alert_level == "RED":
        return f"🚨 CRITICAL: {conditions_str.upper()} detected. Immediate intervention required."
    elif alert_level == "ORANGE":
        return f"⚠️ URGENT: {conditions_str} identified. Prompt evaluation needed."
    elif alert_level == "YELLOW":
        return f"📋 FOLLOW-UP: {conditions_str} noted. Schedule appropriate follow-up."
    else:
        return f"ℹ️ INFO: {conditions_str} observed."


@pw.udf
def get_treatment_recommendations(conditions: list) -> list:
    """UDF to get evidence-based treatment recommendations"""
    
    recommendations = []
    
    for condition in conditions:
        condition_lower = condition.lower()
        
        if "pulmonary embolism" in condition_lower:
            recommendations.extend([
                "Initiate anticoagulation therapy immediately",
                "Consider thrombolytic therapy if massive PE",
                "Monitor oxygen saturation and blood pressure"
            ])
        elif "aortic dissection" in condition_lower:
            recommendations.extend([
                "Control blood pressure (SBP <120 mmHg)",
                "Urgent cardiothoracic surgery consultation",
                "Prepare for emergency surgery"
            ])
        elif any(word in condition_lower for word in ["hemorrhage", "bleed", "hematoma"]):
            recommendations.extend([
                "Type and crossmatch blood products",
                "Consider reversal agents if on anticoagulation",
                "Neurosurgical consultation if intracranial"
            ])
        elif "pneumothorax" in condition_lower:
            recommendations.extend([
                "Chest tube placement if tension pneumothorax",
                "Serial chest X-rays",
                "Monitor respiratory status"
            ])
        elif "fracture" in condition_lower:
            recommendations.extend([
                "Immobilize affected area",
                "Orthopedic consultation if displaced",
                "Pain management protocol"
            ])
        elif "mass" in condition_lower:
            recommendations.extend([
                "Further characterization with contrast study",
                "Oncology consultation",
                "Tissue sampling consideration"
            ])
    
    # Remove duplicates
    return list(set(recommendations)) if recommendations else ["Standard follow-up care"]


@pw.udf  
def estimate_treatment_urgency(alert_level: str) -> int:
    """UDF to estimate treatment urgency in minutes"""
    
    urgency_map = {
        "RED": 15,      # 15 minutes max
        "ORANGE": 60,   # 1 hour
        "YELLOW": 240,  # 4 hours
        "GREEN": 1440   # 24 hours
    }
    
    return urgency_map.get(alert_level, 1440)


@pw.udf
def calculate_hourly_processing_rate() -> float:
    """UDF to calculate documents processed per hour"""
    # This would be implemented with proper time window calculations
    # For now, return a placeholder that would be calculated from actual timestamps
    return 0.0


class PathwayDocumentService:
    """Service to orchestrate document processing pipelines"""
    
    def __init__(self, landingai_api_key: str):
        self.processor = PathwayDocumentProcessor(landingai_api_key)
        self.is_running = False
    
    def start_document_processing(self, file_stream: pw.Table) -> Dict[str, pw.Table]:
        """Start document processing pipeline and return output streams"""
        
        # Main processing pipeline
        critical_alerts = self.processor.create_document_processing_pipeline(file_stream)
        
        # Statistics pipeline
        processing_stats = self.processor.create_processing_statistics_pipeline(critical_alerts)
        
        # Set up output streams
        output_streams = {
            "critical_alerts": critical_alerts,
            "processing_stats": processing_stats
        }
        
        # Output critical alerts for real-time notification
        critical_alerts.debug("critical_alerts_stream")
        
        # Output processing statistics
        processing_stats.debug("processing_statistics")
        
        self.is_running = True
        logger.info("Started Pathway document processing pipeline")
        
        return output_streams
    
    def create_alert_escalation_pipeline(self, alerts_stream: pw.Table) -> pw.Table:
        """Create alert escalation pipeline for unacknowledged alerts"""
        
        # Add escalation timing
        alerts_with_escalation = alerts_stream.select(
            *pw.this,
            escalation_time=calculate_escalation_time(
                pw.this.alert_level,
                pw.this.timestamp
            ),
            needs_escalation=check_escalation_needed(
                pw.this.alert_level,
                pw.this.timestamp
            )
        )
        
        return alerts_with_escalation


@pw.udf
def calculate_escalation_time(alert_level: str, timestamp: str) -> str:
    """UDF to calculate when alert should be escalated"""
    
    try:
        from datetime import datetime, timedelta
        
        alert_time = datetime.fromisoformat(timestamp)
        
        escalation_minutes = {
            "RED": 5,      # 5 minutes
            "ORANGE": 15,  # 15 minutes
            "YELLOW": 60   # 1 hour
        }
        
        minutes_to_add = escalation_minutes.get(alert_level, 60)
        escalation_time = alert_time + timedelta(minutes=minutes_to_add)
        
        return escalation_time.isoformat()
        
    except Exception as e:
        logger.error(f"Error calculating escalation time: {e}")
        return timestamp


@pw.udf
def check_escalation_needed(alert_level: str, timestamp: str) -> bool:
    """UDF to check if alert needs escalation"""
    
    try:
        from datetime import datetime
        
        if alert_level not in ["RED", "ORANGE"]:
            return False
        
        alert_time = datetime.fromisoformat(timestamp)
        current_time = datetime.now()
        
        time_elapsed = (current_time - alert_time).total_seconds() / 60  # minutes
        
        escalation_thresholds = {
            "RED": 5,      # 5 minutes
            "ORANGE": 15   # 15 minutes
        }
        
        threshold = escalation_thresholds.get(alert_level, 60)
        
        return time_elapsed >= threshold
        
    except Exception as e:
        logger.error(f"Error checking escalation: {e}")
        return False

