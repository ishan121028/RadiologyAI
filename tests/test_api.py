"""
Test suite for CriticalAlert AI API endpoints

Tests the RAG-based query system, document search, and alert functionality
"""

import pytest
import requests
import json
import time
from typing import Dict, Any


class TestCriticalAlertAPI:
    """Test suite for CriticalAlert AI REST API"""
    
    BASE_URL = "http://localhost:49001"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        # Wait a moment to ensure API is ready
        time.sleep(0.1)
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "CriticalAlert AI"
        assert data["streaming"] == "active"
        assert "/api/query" in data["endpoints"]
        assert "/api/search" in data["endpoints"]
        assert "/health" in data["endpoints"]
    
    def test_query_endpoint_elbow_xray(self):
        """Test RAG query for elbow X-ray findings"""
        payload = {
            "query": "What are the findings for the elbow x-ray?"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["query"] == payload["query"]
        assert data["status"] == "success"
        assert "medical_response" in data
        assert "medical_context" in data
        assert "alert_level" in data
        assert "recommendations" in data
        assert "rag_info" in data
        
        # Verify content for elbow X-ray
        assert "elbow" in data["medical_context"].lower()
        assert "normal" in data["medical_response"].lower()
        assert data["alert_level"] == "GREEN"
        assert data["alerts_found"] == 0
        
        # Verify RAG info
        assert data["rag_info"]["documents_retrieved"] >= 1
        assert "x ray elbow joint report format - drlogy (1).pdf" in data["rag_info"]["sources"]
    
    def test_query_endpoint_renal_ultrasound(self):
        """Test RAG query for renal ultrasound concerns"""
        payload = {
            "query": "Are there any concerns with the kidney ultrasound?"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["query"] == payload["query"]
        assert data["status"] == "success"
        
        # Verify content for renal ultrasound
        assert "renal" in data["medical_context"].lower() or "kidney" in data["medical_context"].lower()
        assert "scarring" in data["medical_response"].lower()
        assert data["alert_level"] == "YELLOW"  # Should be elevated due to scarring
        assert data["alerts_found"] == 1
        
        # Verify recommendations for YELLOW alert
        assert any("follow-up" in rec.lower() or "monitor" in rec.lower() for rec in data["recommendations"])
        
        # Verify RAG info
        assert data["rag_info"]["documents_retrieved"] >= 1
        assert "Renal-Ultrasound.pdf" in data["rag_info"]["sources"]
    
    def test_query_endpoint_no_match(self):
        """Test RAG query for content not in documents"""
        payload = {
            "query": "What about brain MRI findings?"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return success with help information
        assert data["status"] == "success"
        assert data["alert_level"] == "GREEN"
        assert "available extracted reports" in data["medical_context"].lower()
    
    def test_search_endpoint_elbow(self):
        """Test document search for elbow X-ray"""
        payload = {
            "query": "x ray elbow joint",
            "limit": 3
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["query"] == payload["query"]
        assert data["status"] == "success"
        assert data["results_count"] >= 1
        assert len(data["documents"]) >= 1
        
        # Verify document content
        doc = data["documents"][0]
        assert "content" in doc
        assert "metadata" in doc
        assert "relevance_score" in doc
        
        # Verify elbow X-ray content
        assert "elbow" in doc["content"].lower()
        assert "yashvi m. patel" in doc["content"].lower()
        assert doc["metadata"]["type"] == "x_ray_report"
        assert doc["metadata"]["alert_level"] == "GREEN"
        assert doc["relevance_score"] > 0.9
    
    def test_search_endpoint_renal(self):
        """Test document search for renal ultrasound"""
        payload = {
            "query": "renal ultrasound kidney",
            "limit": 3
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["status"] == "success"
        assert data["results_count"] >= 1
        
        # Verify renal ultrasound content
        doc = data["documents"][0]
        assert "renal" in doc["content"].lower()
        assert "scarring" in doc["content"].lower()
        assert doc["metadata"]["type"] == "ultrasound_report"
        assert doc["metadata"]["alert_level"] == "YELLOW"
        assert doc["metadata"]["clinical_history"] == "Hematuria, Glomerulonephritis"
    
    def test_search_endpoint_no_match(self):
        """Test document search with no matching content"""
        payload = {
            "query": "brain MRI scan",
            "limit": 3
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return help information
        assert data["status"] == "success"
        assert data["results_count"] >= 1
        doc = data["documents"][0]
        assert "no specific matches found" in doc["content"].lower()
        assert doc["metadata"]["type"] == "search_help"
    
    def test_alert_levels_consistency(self):
        """Test that alert levels are consistent between query and search endpoints"""
        
        # Test elbow X-ray (should be GREEN)
        query_response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": "elbow x-ray findings"})
        )
        
        search_response = requests.post(
            f"{self.BASE_URL}/api/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": "elbow x-ray", "limit": 1})
        )
        
        assert query_response.status_code == 200
        assert search_response.status_code == 200
        
        query_alert = query_response.json()["alert_level"]
        search_alert = search_response.json()["documents"][0]["metadata"]["alert_level"]
        
        assert query_alert == search_alert == "GREEN"
        
        # Test renal ultrasound (should be YELLOW)
        query_response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": "kidney ultrasound concerns"})
        )
        
        search_response = requests.post(
            f"{self.BASE_URL}/api/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": "renal ultrasound", "limit": 1})
        )
        
        assert query_response.status_code == 200
        assert search_response.status_code == 200
        
        query_alert = query_response.json()["alert_level"]
        search_alert = search_response.json()["documents"][0]["metadata"]["alert_level"]
        
        assert query_alert == search_alert == "YELLOW"
    
    def test_contextual_intelligence(self):
        """Test that the system provides contextual medical responses"""
        
        test_cases = [
            {
                "query": "What are the findings?",
                "expected_keywords": ["findings", "normal", "elbow"],
                "description": "General findings query should return elbow results"
            },
            {
                "query": "Are there any concerns?",
                "expected_keywords": ["concern", "scarring", "kidney"],
                "description": "Concern query should return renal scarring info"
            },
            {
                "query": "What are the recommendations?",
                "expected_keywords": ["recommend", "follow", "monitor"],
                "description": "Recommendation query should provide medical advice"
            }
        ]
        
        for case in test_cases:
            response = requests.post(
                f"{self.BASE_URL}/api/query",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"query": case["query"]})
            )
            
            assert response.status_code == 200, f"Failed for query: {case['query']}"
            data = response.json()
            
            # Check that response contains expected contextual keywords
            response_text = data["medical_response"].lower()
            found_keywords = [kw for kw in case["expected_keywords"] if kw in response_text]
            
            assert len(found_keywords) > 0, f"No expected keywords found in response for: {case['description']}"
    
    def test_rag_information_tracking(self):
        """Test that RAG information is properly tracked"""
        payload = {
            "query": "Tell me about the medical reports"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify RAG tracking information
        rag_info = data["rag_info"]
        assert "documents_retrieved" in rag_info
        assert "sources" in rag_info
        assert "relevance_scores" in rag_info
        assert "method" in rag_info
        
        assert rag_info["documents_retrieved"] > 0
        assert len(rag_info["sources"]) > 0
        assert len(rag_info["relevance_scores"]) > 0
        assert rag_info["method"] == "document_retrieval_with_llm_analysis"
    
    def test_error_handling(self):
        """Test API error handling"""
        
        # Test malformed JSON
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        assert response.status_code == 400
        
        # Test missing required fields
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps({})
        )
        assert response.status_code == 400
        
        # Test missing required fields for search
        response = requests.post(
            f"{self.BASE_URL}/api/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"limit": 5})  # Missing query
        )
        assert response.status_code == 400


class TestAlertSystem:
    """Test suite specifically for the alert system functionality"""
    
    BASE_URL = "http://localhost:49001"
    
    def test_green_alert_conditions(self):
        """Test conditions that should generate GREEN alerts"""
        green_queries = [
            "normal elbow findings",
            "no abnormalities detected",
            "routine x-ray results"
        ]
        
        for query in green_queries:
            response = requests.post(
                f"{self.BASE_URL}/api/query",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"query": query})
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should be GREEN alert with no alerts found
            if data["alert_level"] != "GREEN":
                # Some queries might not match any documents and return help
                assert "available extracted reports" in data["medical_context"].lower()
    
    def test_yellow_alert_conditions(self):
        """Test conditions that should generate YELLOW alerts"""
        yellow_queries = [
            "kidney scarring concerns",
            "renal cortical findings",
            "ultrasound abnormalities"
        ]
        
        for query in yellow_queries:
            response = requests.post(
                f"{self.BASE_URL}/api/query",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"query": query})
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should be YELLOW alert for renal scarring
            if "renal" in data["medical_context"].lower() or "kidney" in data["medical_context"].lower():
                assert data["alert_level"] == "YELLOW"
                assert data["alerts_found"] >= 1
                assert any("follow-up" in rec.lower() or "monitor" in rec.lower() for rec in data["recommendations"])
    
    def test_alert_recommendations(self):
        """Test that appropriate recommendations are provided for each alert level"""
        
        # Test GREEN alert recommendations
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": "elbow x-ray normal findings"})
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["alert_level"] == "GREEN":
                assert "standard" in " ".join(data["recommendations"]).lower()
        
        # Test YELLOW alert recommendations  
        response = requests.post(
            f"{self.BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": "kidney scarring concerns"})
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["alert_level"] == "YELLOW":
                recommendations_text = " ".join(data["recommendations"]).lower()
                assert any(keyword in recommendations_text for keyword in ["follow-up", "monitor", "24 hours"])


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
