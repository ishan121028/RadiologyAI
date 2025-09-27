import asyncio
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
import hashlib
import logging

logger = logging.getLogger(__name__)


class FilesystemManager:
    """Manages filesystem structure for radiology report processing"""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_dir = Path(base_data_dir)
        self.directories = {
            "incoming": self.base_dir / "incoming",
            "processing": self.base_dir / "processing", 
            "processed": self.base_dir / "processed",
            "alerts": self.base_dir / "alerts",
            "archive": self.base_dir / "archive",
            "failed": self.base_dir / "failed",
            "metadata": self.base_dir / "metadata"
        }
        
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """Create required directory structure"""
        for dir_name, dir_path in self.directories.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Create subdirectories for processed files by date
        processed_today = self.directories["processed"] / datetime.now().strftime("%Y/%m/%d")
        processed_today.mkdir(parents=True, exist_ok=True)
        
        # Create alert level subdirectories
        alert_levels = ["red", "orange", "yellow", "green"]
        for level in alert_levels:
            (self.directories["alerts"] / level).mkdir(exist_ok=True)
    
    def get_incoming_directory(self) -> Path:
        """Get the directory where new radiology reports arrive"""
        return self.directories["incoming"]
    
    def get_processing_directory(self) -> Path:
        """Get the directory for files currently being processed"""
        return self.directories["processing"]
    
    def move_to_processing(self, file_path: Path) -> Path:
        """Move file from incoming to processing directory"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        processing_path = self.directories["processing"] / file_path.name
        
        # Handle duplicate filenames
        counter = 1
        original_path = processing_path
        while processing_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            processing_path = self.directories["processing"] / f"{stem}_{counter}{suffix}"
            counter += 1
        
        shutil.move(str(file_path), str(processing_path))
        logger.info(f"Moved {file_path.name} to processing: {processing_path.name}")
        
        return processing_path
    
    def move_to_processed(self, file_path: Path, alert_level: str = "green") -> Path:
        """Move processed file to appropriate archive location"""
        today_dir = self.directories["processed"] / datetime.now().strftime("%Y/%m/%d")
        today_dir.mkdir(parents=True, exist_ok=True)
        
        processed_path = today_dir / file_path.name
        
        # Handle duplicates
        counter = 1
        original_path = processed_path
        while processed_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            processed_path = today_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        shutil.move(str(file_path), str(processed_path))
        
        # Also copy to alert level directory if critical
        if alert_level in ["red", "orange"]:
            alert_dir = self.directories["alerts"] / alert_level
            alert_path = alert_dir / file_path.name
            
            counter = 1
            original_alert_path = alert_path
            while alert_path.exists():
                stem = original_alert_path.stem
                suffix = original_alert_path.suffix
                alert_path = alert_dir / f"{stem}_{counter}{suffix}"
                counter += 1
                
            shutil.copy2(str(processed_path), str(alert_path))
            logger.info(f"Copied critical file to alerts/{alert_level}: {alert_path.name}")
        
        logger.info(f"Moved {file_path.name} to processed: {processed_path}")
        return processed_path
    
    def move_to_failed(self, file_path: Path, error_reason: str) -> Path:
        """Move failed file to failed directory with error log"""
        failed_path = self.directories["failed"] / file_path.name
        
        # Handle duplicates
        counter = 1
        original_path = failed_path
        while failed_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            failed_path = self.directories["failed"] / f"{stem}_{counter}{suffix}"
            counter += 1
        
        shutil.move(str(file_path), str(failed_path))
        
        # Create error log
        error_log_path = failed_path.with_suffix(failed_path.suffix + ".error")
        error_info = {
            "original_file": file_path.name,
            "error_reason": error_reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_size": failed_path.stat().st_size if failed_path.exists() else 0
        }
        
        with open(error_log_path, 'w') as f:
            json.dump(error_info, f, indent=2)
        
        logger.error(f"Moved {file_path.name} to failed: {error_reason}")
        return failed_path
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for duplicate detection"""
        hash_md5 = hashlib.md5()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
            
        return hash_md5.hexdigest()
    
    def is_duplicate_file(self, file_path: Path) -> bool:
        """Check if file is a duplicate based on hash"""
        current_hash = self.calculate_file_hash(file_path)
        
        if not current_hash:
            return False
        
        # Check against processed files metadata
        metadata_dir = self.directories["metadata"]
        hash_file = metadata_dir / "processed_hashes.json"
        
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    processed_hashes = json.load(f)
                    
                if current_hash in processed_hashes:
                    logger.warning(f"Duplicate file detected: {file_path.name} (matches {processed_hashes[current_hash]})")
                    return True
            except Exception as e:
                logger.error(f"Error reading processed hashes: {e}")
        
        return False
    
    def record_processed_file(self, file_path: Path, processing_result: Dict):
        """Record file processing result in metadata"""
        file_hash = self.calculate_file_hash(file_path)
        
        if not file_hash:
            return
        
        metadata_dir = self.directories["metadata"]
        
        # Update hash registry
        hash_file = metadata_dir / "processed_hashes.json"
        processed_hashes = {}
        
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    processed_hashes = json.load(f)
            except Exception as e:
                logger.error(f"Error loading processed hashes: {e}")
        
        processed_hashes[file_hash] = file_path.name
        
        try:
            with open(hash_file, 'w') as f:
                json.dump(processed_hashes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed hashes: {e}")
        
        # Record detailed processing metadata
        processing_metadata = {
            "filename": file_path.name,
            "file_hash": file_hash,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_result": processing_result,
            "alert_level": processing_result.get("alert_level", "unknown")
        }
        
        metadata_file = metadata_dir / f"{file_path.stem}_metadata.json"
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(processing_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processing metadata: {e}")
    
    def get_processing_statistics(self) -> Dict:
        """Get filesystem processing statistics"""
        stats = {
            "directories": {},
            "total_files": 0,
            "processing_queue_size": 0,
            "alerts_by_level": {},
            "failed_files": 0
        }
        
        for dir_name, dir_path in self.directories.items():
            if dir_path.exists():
                files = list(dir_path.glob("*"))
                file_count = len([f for f in files if f.is_file()])
                stats["directories"][dir_name] = file_count
                stats["total_files"] += file_count
        
        # Count files in processing queue
        if self.directories["processing"].exists():
            processing_files = list(self.directories["processing"].glob("*.pdf"))
            stats["processing_queue_size"] = len(processing_files)
        
        # Count alerts by level
        alert_levels = ["red", "orange", "yellow", "green"]
        for level in alert_levels:
            alert_dir = self.directories["alerts"] / level
            if alert_dir.exists():
                alert_files = list(alert_dir.glob("*.pdf"))
                stats["alerts_by_level"][level] = len(alert_files)
        
        # Count failed files
        if self.directories["failed"].exists():
            failed_files = list(self.directories["failed"].glob("*.pdf"))
            stats["failed_files"] = len(failed_files)
        
        return stats
    
    def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up old processed files beyond retention period"""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        cleanup_dirs = [
            self.directories["processed"],
            self.directories["archive"],
            self.directories["failed"]
        ]
        
        files_cleaned = 0
        
        for cleanup_dir in cleanup_dirs:
            if not cleanup_dir.exists():
                continue
                
            for file_path in cleanup_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        if file_path.stat().st_mtime < cutoff_date:
                            file_path.unlink()
                            files_cleaned += 1
                            logger.info(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {file_path}: {e}")
        
        # Clean up empty directories
        for cleanup_dir in cleanup_dirs:
            if cleanup_dir.exists():
                try:
                    for dir_path in cleanup_dir.rglob("*"):
                        if dir_path.is_dir() and not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            logger.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logger.error(f"Error removing empty directories: {e}")
        
        logger.info(f"Cleanup completed. Removed {files_cleaned} old files.")
        return files_cleaned
    
    def validate_file(self, file_path: Path) -> Dict:
        """Validate incoming radiology report file"""
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "file_info": {}
        }
        
        try:
            # Check if file exists
            if not file_path.exists():
                validation_result["errors"].append("File does not exist")
                return validation_result
            
            # Check file size (minimum 1KB, maximum 50MB)
            file_size = file_path.stat().st_size
            validation_result["file_info"]["size_bytes"] = file_size
            
            if file_size < 1024:  # Less than 1KB
                validation_result["errors"].append("File too small (less than 1KB)")
            elif file_size > 50 * 1024 * 1024:  # More than 50MB
                validation_result["errors"].append("File too large (more than 50MB)")
            
            # Check file extension
            if file_path.suffix.lower() != '.pdf':
                validation_result["errors"].append("File must be PDF format")
            
            # Check if file is readable
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    if not header.startswith(b'%PDF'):
                        validation_result["errors"].append("File does not appear to be a valid PDF")
            except Exception as e:
                validation_result["errors"].append(f"Cannot read file: {str(e)}")
            
            # Check for duplicate
            if self.is_duplicate_file(file_path):
                validation_result["warnings"].append("File appears to be a duplicate")
            
            # Add file metadata
            stat = file_path.stat()
            validation_result["file_info"].update({
                "filename": file_path.name,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_hash": self.calculate_file_hash(file_path)
            })
            
            # File is valid if no errors
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
