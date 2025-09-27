import pathway as pw
from pathlib import Path
from typing import Dict, Optional
import hashlib
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RadiologyFileSchema(pw.Schema):
    filename: str
    filepath: str
    file_size: int
    file_hash: str
    timestamp: str
    content: bytes


class ProcessingResultSchema(pw.Schema):
    filename: str
    filepath: str
    processing_status: str
    alert_level: str
    critical_findings: str
    processing_time: float
    error_message: str
    timestamp: str


class RadiologyFileConnector:
    """Pathway-based real-time file monitoring and processing connector"""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_dir = Path(base_data_dir)
        self.incoming_dir = self.base_dir / "incoming"
        self.processed_dir = self.base_dir / "processed"
        self.failed_dir = self.base_dir / "failed"
        
        # Ensure directories exist
        for directory in [self.incoming_dir, self.processed_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def create_file_stream(self) -> pw.Table:
        """Create Pathway table for streaming radiology files"""
        
        # Monitor incoming directory for new PDF files
        files_stream = pw.io.fs.read(
            path=str(self.incoming_dir),
            format="binary",
            with_metadata=True,
            mode="streaming"
        )
        
        return files_stream
    
    def create_processing_pipeline(self) -> pw.Table:
        """Create complete Pathway processing pipeline"""
        
        # Step 1: Stream incoming files
        raw_files = self.create_file_stream()
        
        # Step 2: Apply validation UDF
        validated_files = raw_files.select(
            *pw.this,
            validation_result=validate_radiology_file(
                pw.this.data,
                pw.this._metadata["path"]
            )
        )
        
        # Step 3: Filter valid files only
        valid_files = validated_files.filter(
            pw.this.validation_result["is_valid"] == True
        )
        
        # Step 4: Check for duplicates
        deduplicated_files = valid_files.select(
            *pw.this,
            is_duplicate=check_duplicate_file(
                pw.this.validation_result["file_hash"]
            )
        )
        
        # Step 5: Prepare for processing
        ready_for_processing = deduplicated_files.filter(
            pw.this.is_duplicate == False
        ).select(
            filename=extract_filename(pw.this._metadata["path"]),
            filepath=pw.this._metadata["path"],
            file_size=pw.this._metadata["size"],
            file_hash=pw.this.validation_result["file_hash"],
            content=pw.this.data,
            timestamp=pw.now(),
            processing_status="ready"
        )
        
        return ready_for_processing


# Custom Pathway UDFs
@pw.udf
def validate_radiology_file(file_data: bytes, file_path: str) -> dict:
    """UDF to validate radiology report file"""
    
    validation_result = {
        "is_valid": False,
        "file_hash": "",
        "errors": [],
        "warnings": [],
        "file_info": {}
    }
    
    try:
        path = Path(file_path)
        
        # Check file extension
        if path.suffix.lower() != '.pdf':
            validation_result["errors"].append("File must be PDF format")
        
        # Check file size (1KB to 50MB)
        file_size = len(file_data)
        if file_size < 1024:
            validation_result["errors"].append("File too small (less than 1KB)")
        elif file_size > 50 * 1024 * 1024:
            validation_result["errors"].append("File too large (more than 50MB)")
        
        # Check PDF header
        if not file_data.startswith(b'%PDF'):
            validation_result["errors"].append("Not a valid PDF file")
        
        # Calculate file hash for duplicate detection
        validation_result["file_hash"] = hashlib.md5(file_data).hexdigest()
        
        # Add file metadata
        validation_result["file_info"] = {
            "filename": path.name,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2)
        }
        
        # File is valid if no errors
        validation_result["is_valid"] = len(validation_result["errors"]) == 0
        
        if validation_result["is_valid"]:
            logger.info(f"Validated file: {path.name}")
        else:
            logger.warning(f"Invalid file {path.name}: {', '.join(validation_result['errors'])}")
            
    except Exception as e:
        validation_result["errors"].append(f"Validation error: {str(e)}")
        logger.error(f"Error validating file {file_path}: {e}")
    
    return validation_result


@pw.udf  
def check_duplicate_file(file_hash: str) -> bool:
    """UDF to check if file is a duplicate based on hash"""
    
    try:
        # Check against stored hashes (in practice, this would be a proper database/cache)
        hash_file = Path("data/metadata/processed_hashes.json")
        
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                processed_hashes = json.load(f)
                
            if file_hash in processed_hashes:
                logger.warning(f"Duplicate file detected with hash: {file_hash}")
                return True
                
    except Exception as e:
        logger.error(f"Error checking duplicate hash {file_hash}: {e}")
    
    return False


@pw.udf
def extract_filename(file_path: str) -> str:
    """UDF to extract filename from path"""
    return Path(file_path).name


@pw.udf
def calculate_processing_time(start_time: str) -> float:
    """UDF to calculate processing time in seconds"""
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.now()
        return (end - start).total_seconds()
    except Exception:
        return 0.0


@pw.udf
def move_processed_file(filepath: str, alert_level: str) -> dict:
    """UDF to move processed file to appropriate directory"""
    
    result = {
        "moved": False,
        "new_path": "",
        "error": ""
    }
    
    try:
        source_path = Path(filepath)
        
        if not source_path.exists():
            result["error"] = "Source file does not exist"
            return result
        
        # Determine target directory based on alert level
        base_dir = Path("data")
        
        if alert_level in ["red", "orange"]:
            target_dir = base_dir / "alerts" / alert_level
        else:
            # Use date-based directory structure
            today = datetime.now().strftime("%Y/%m/%d")
            target_dir = base_dir / "processed" / today
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle duplicate filenames
        target_path = target_dir / source_path.name
        counter = 1
        original_target = target_path
        
        while target_path.exists():
            stem = original_target.stem
            suffix = original_target.suffix
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # Move file
        import shutil
        shutil.move(str(source_path), str(target_path))
        
        result["moved"] = True
        result["new_path"] = str(target_path)
        
        logger.info(f"Moved file {source_path.name} to {target_path}")
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error moving file {filepath}: {e}")
    
    return result


@pw.udf
def record_processing_metadata(filename: str, processing_result: dict) -> bool:
    """UDF to record processing metadata"""
    
    try:
        metadata_dir = Path("data/metadata")
        metadata_dir.mkdir(exist_ok=True)
        
        # Update processed hashes
        hash_file = metadata_dir / "processed_hashes.json"
        processed_hashes = {}
        
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                processed_hashes = json.load(f)
        
        file_hash = processing_result.get("file_hash", "")
        if file_hash:
            processed_hashes[file_hash] = filename
            
            with open(hash_file, 'w') as f:
                json.dump(processed_hashes, f, indent=2)
        
        # Save detailed processing metadata
        metadata_file = metadata_dir / f"{Path(filename).stem}_metadata.json"
        
        processing_metadata = {
            "filename": filename,
            "processing_timestamp": datetime.now().isoformat(),
            "processing_result": processing_result
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(processing_metadata, f, indent=2)
        
        logger.info(f"Recorded metadata for {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error recording metadata for {filename}: {e}")
        return False


class PathwayFileProcessor:
    """Main Pathway-based file processing engine"""
    
    def __init__(self):
        self.connector = RadiologyFileConnector()
        self.processing_stats = {
            "files_processed": 0,
            "critical_alerts_generated": 0,
            "processing_errors": 0
        }
    
    def create_monitoring_pipeline(self) -> pw.Table:
        """Create the main file monitoring and processing pipeline"""
        
        # Get the base file processing pipeline
        ready_files = self.connector.create_processing_pipeline()
        
        # Add processing timestamp
        processing_pipeline = ready_files.select(
            *pw.this,
            processing_started=pw.now()
        )
        
        return processing_pipeline
    
    def create_error_handling_pipeline(self, main_pipeline: pw.Table) -> pw.Table:
        """Create error handling pipeline for failed files"""
        
        # This would typically catch processing errors and route to failed directory
        error_pipeline = main_pipeline.select(
            *pw.this,
            error_handling_result=handle_processing_errors(
                pw.this.filepath,
                pw.this.processing_status
            )
        )
        
        return error_pipeline
    
    def create_statistics_pipeline(self, main_pipeline: pw.Table) -> pw.Table:
        """Create pipeline for real-time processing statistics"""
        
        # Count processed files by status
        stats_pipeline = main_pipeline.groupby().reduce(
            total_files=pw.reducers.count(),
            avg_file_size=pw.reducers.avg(pw.this.file_size),
            processing_rate_per_minute=calculate_processing_rate(),
            last_processed=pw.reducers.latest(pw.this.timestamp)
        )
        
        return stats_pipeline


@pw.udf
def handle_processing_errors(filepath: str, status: str) -> dict:
    """UDF to handle processing errors"""
    
    result = {
        "error_handled": False,
        "action_taken": "",
        "error_details": ""
    }
    
    try:
        if status == "error" or status == "failed":
            source_path = Path(filepath)
            
            if source_path.exists():
                failed_dir = Path("data/failed")
                failed_dir.mkdir(exist_ok=True)
                
                target_path = failed_dir / source_path.name
                
                # Handle duplicates
                counter = 1
                original_target = target_path
                while target_path.exists():
                    stem = original_target.stem
                    suffix = original_target.suffix
                    target_path = failed_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Move file
                import shutil
                shutil.move(str(source_path), str(target_path))
                
                # Create error log
                error_log_path = target_path.with_suffix(target_path.suffix + ".error")
                error_info = {
                    "original_file": source_path.name,
                    "error_timestamp": datetime.now().isoformat(),
                    "status": status
                }
                
                with open(error_log_path, 'w') as f:
                    json.dump(error_info, f, indent=2)
                
                result["error_handled"] = True
                result["action_taken"] = f"Moved to failed directory: {target_path}"
                
                logger.info(f"Handled error for {source_path.name}")
                
    except Exception as e:
        result["error_details"] = str(e)
        logger.error(f"Error handling failed file {filepath}: {e}")
    
    return result


@pw.udf
def calculate_processing_rate() -> float:
    """UDF to calculate files processed per minute"""
    # This would be implemented with proper time window calculations
    # For now, return a placeholder
    return 0.0


class PathwayStreamingService:
    """Service to run Pathway streaming pipelines"""
    
    def __init__(self):
        self.processor = PathwayFileProcessor()
        self.is_running = False
    
    def start_monitoring(self):
        """Start the Pathway streaming pipeline"""
        
        # Create the main processing pipeline
        main_pipeline = self.processor.create_monitoring_pipeline()
        
        # Add error handling
        error_handled_pipeline = self.processor.create_error_handling_pipeline(main_pipeline)
        
        # Add statistics tracking
        stats_pipeline = self.processor.create_statistics_pipeline(error_handled_pipeline)
        
        # Set up output connectors for processed files
        # This would connect to the next stage (LandingAI parsing)
        processing_output = error_handled_pipeline.select(
            filename=pw.this.filename,
            filepath=pw.this.filepath,
            content=pw.this.content,
            ready_for_parsing=pw.this.processing_status == "ready",
            timestamp=pw.this.timestamp
        )
        
        # In a real implementation, this would output to the next processing stage
        # For now, we'll log the results
        processing_output.debug("radiology_files_ready")
        
        self.is_running = True
        logger.info("Started Pathway streaming pipeline for radiology file monitoring")
        
        # Run the Pathway computation
        pw.run()
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.is_running = False
        logger.info("Stopped Pathway streaming pipeline")
