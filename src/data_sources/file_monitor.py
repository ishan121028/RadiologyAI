import asyncio
import time
from pathlib import Path
from typing import AsyncGenerator, Callable, Dict, List, Optional, Set
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
import logging

logger = logging.getLogger(__name__)


class RadiologyFileHandler(FileSystemEventHandler):
    """Handle filesystem events for radiology reports"""
    
    def __init__(self, callback: Callable[[Path], None]):
        super().__init__()
        self.callback = callback
        self.processed_files: Set[str] = set()
        self.file_settle_time = 2  # Wait 2 seconds for file to be completely written
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and self._is_radiology_file(event.src_path):
            asyncio.create_task(self._handle_file_event(event.src_path))
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and self._is_radiology_file(event.src_path):
            asyncio.create_task(self._handle_file_event(event.src_path))
    
    def _is_radiology_file(self, file_path: str) -> bool:
        """Check if file is a radiology report PDF"""
        path = Path(file_path)
        
        # Check file extension
        if path.suffix.lower() != '.pdf':
            return False
        
        # Skip temporary files and system files
        if path.name.startswith('.') or path.name.startswith('~'):
            return False
        
        # Skip already processed files
        if file_path in self.processed_files:
            return False
        
        return True
    
    async def _handle_file_event(self, file_path: str):
        """Handle file event with settling time"""
        # Wait for file to be completely written
        await asyncio.sleep(self.file_settle_time)
        
        path = Path(file_path)
        
        # Check if file still exists and is complete
        if not path.exists():
            return
        
        # Check if file size is stable (not still being written)
        initial_size = path.stat().st_size
        await asyncio.sleep(0.5)
        
        if not path.exists():
            return
            
        final_size = path.stat().st_size
        
        # If file size changed, it's still being written
        if initial_size != final_size:
            logger.debug(f"File still being written: {path.name}")
            # Retry after more time
            await asyncio.sleep(2)
            await self._handle_file_event(file_path)
            return
        
        # File is stable, process it
        if file_path not in self.processed_files:
            self.processed_files.add(file_path)
            logger.info(f"New radiology file detected: {path.name}")
            
            try:
                await self.callback(path)
            except Exception as e:
                logger.error(f"Error processing file {path.name}: {e}")
                # Remove from processed set so it can be retried
                self.processed_files.discard(file_path)


class FileMonitor:
    """Monitor filesystem for new radiology report PDFs"""
    
    def __init__(self, watch_directory: str, filesystem_manager):
        self.watch_dir = Path(watch_directory)
        self.filesystem_manager = filesystem_manager
        self.observer = None
        self.is_monitoring = False
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
        
        # Callbacks for processing pipeline
        self.file_processors: List[Callable[[Path], None]] = []
        
        # Ensure watch directory exists
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
    def add_file_processor(self, processor: Callable[[Path], None]):
        """Add a file processor callback"""
        self.file_processors.append(processor)
    
    async def start_monitoring(self):
        """Start monitoring the directory for new files"""
        if self.is_monitoring:
            logger.warning("File monitoring already started")
            return
        
        self.start_time = datetime.now()
        self.is_monitoring = True
        
        # Set up watchdog observer
        event_handler = RadiologyFileHandler(self._process_new_file)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        
        logger.info(f"Started monitoring directory: {self.watch_dir}")
        
        # Process any existing files in the directory
        await self._process_existing_files()
        
        # Keep monitoring running
        try:
            while self.is_monitoring:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Stop monitoring the directory"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        logger.info("Stopped file monitoring")
    
    async def _process_existing_files(self):
        """Process any existing PDF files in the watch directory"""
        try:
            pdf_files = list(self.watch_dir.glob("*.pdf"))
            
            if pdf_files:
                logger.info(f"Found {len(pdf_files)} existing PDF files to process")
                
                for pdf_file in pdf_files:
                    try:
                        await self._process_new_file(pdf_file)
                    except Exception as e:
                        logger.error(f"Error processing existing file {pdf_file.name}: {e}")
        except Exception as e:
            logger.error(f"Error scanning existing files: {e}")
    
    async def _process_new_file(self, file_path: Path):
        """Process a new radiology report file"""
        processing_start = time.time()
        
        try:
            logger.info(f"Processing new file: {file_path.name}")
            
            # Validate file
            validation_result = self.filesystem_manager.validate_file(file_path)
            
            if not validation_result["valid"]:
                error_msg = f"File validation failed: {', '.join(validation_result['errors'])}"
                logger.error(f"{file_path.name}: {error_msg}")
                
                # Move to failed directory
                self.filesystem_manager.move_to_failed(file_path, error_msg)
                self.error_count += 1
                return
            
            # Log warnings if any
            if validation_result["warnings"]:
                for warning in validation_result["warnings"]:
                    logger.warning(f"{file_path.name}: {warning}")
            
            # Move to processing directory
            processing_path = self.filesystem_manager.move_to_processing(file_path)
            
            # Create processing metadata
            processing_metadata = {
                "original_filename": file_path.name,
                "processing_started": datetime.now().isoformat(),
                "file_info": validation_result["file_info"],
                "status": "processing"
            }
            
            # Trigger all registered file processors
            for processor in self.file_processors:
                try:
                    await processor(processing_path, processing_metadata)
                except Exception as e:
                    logger.error(f"Error in file processor: {e}")
                    # Continue with other processors
            
            # Update processing statistics
            self.processed_count += 1
            processing_time = time.time() - processing_start
            
            logger.info(f"Successfully processed {file_path.name} in {processing_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}")
            
            # Try to move to failed directory
            try:
                if file_path.exists():
                    self.filesystem_manager.move_to_failed(file_path, str(e))
            except Exception as move_error:
                logger.error(f"Error moving failed file: {move_error}")
            
            self.error_count += 1
    
    def get_monitoring_statistics(self) -> Dict:
        """Get file monitoring statistics"""
        uptime_seconds = 0
        if self.start_time:
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "is_monitoring": self.is_monitoring,
            "watch_directory": str(self.watch_dir),
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "files_processed": self.processed_count,
            "processing_errors": self.error_count,
            "success_rate": (self.processed_count / max(self.processed_count + self.error_count, 1)) * 100,
            "files_per_hour": (self.processed_count / max(uptime_seconds / 3600, 1)) if uptime_seconds > 0 else 0
        }
    
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime seconds into readable string"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours} hours, {minutes} minutes"


class BatchFileProcessor:
    """Process multiple files in batch for initial setup or bulk processing"""
    
    def __init__(self, filesystem_manager):
        self.filesystem_manager = filesystem_manager
        
    async def process_directory_batch(self, source_directory: str, max_files: Optional[int] = None) -> Dict:
        """Process all PDF files in a directory in batch"""
        source_dir = Path(source_directory)
        
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source_directory}")
        
        # Find all PDF files
        pdf_files = list(source_dir.glob("*.pdf"))
        
        if max_files:
            pdf_files = pdf_files[:max_files]
        
        processing_results = {
            "total_files": len(pdf_files),
            "processed_successfully": 0,
            "processing_errors": 0,
            "error_files": [],
            "processing_time": 0
        }
        
        start_time = time.time()
        
        logger.info(f"Starting batch processing of {len(pdf_files)} files from {source_directory}")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_file.name}")
                
                # Validate file
                validation_result = self.filesystem_manager.validate_file(pdf_file)
                
                if not validation_result["valid"]:
                    error_msg = f"Validation failed: {', '.join(validation_result['errors'])}"
                    logger.error(f"{pdf_file.name}: {error_msg}")
                    processing_results["error_files"].append({
                        "filename": pdf_file.name,
                        "error": error_msg
                    })
                    processing_results["processing_errors"] += 1
                    continue
                
                # Copy to incoming directory (preserve original)
                incoming_dir = self.filesystem_manager.get_incoming_directory()
                target_path = incoming_dir / pdf_file.name
                
                # Handle duplicate names
                counter = 1
                original_target = target_path
                while target_path.exists():
                    stem = original_target.stem
                    suffix = original_target.suffix
                    target_path = incoming_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Copy file
                import shutil
                shutil.copy2(pdf_file, target_path)
                
                processing_results["processed_successfully"] += 1
                
                # Add small delay to avoid overwhelming the system
                if i % 10 == 0:  # Every 10 files
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                processing_results["error_files"].append({
                    "filename": pdf_file.name,
                    "error": str(e)
                })
                processing_results["processing_errors"] += 1
        
        processing_results["processing_time"] = time.time() - start_time
        
        logger.info(f"Batch processing completed: {processing_results['processed_successfully']}/{processing_results['total_files']} files processed successfully")
        
        return processing_results
    
    async def simulate_radiology_reports(self, count: int = 10) -> List[Path]:
        """Create simulated radiology report files for testing"""
        incoming_dir = self.filesystem_manager.get_incoming_directory()
        simulated_files = []
        
        sample_report_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
100 700 Td
(RADIOLOGY REPORT - TEST) Tj
0 -20 Td
(Finding: Normal chest X-ray) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000108 00000 n 
0000000178 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
327
%%EOF"""
        
        for i in range(count):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_radiology_report_{timestamp}_{i:03d}.pdf"
            file_path = incoming_dir / filename
            
            # Write simulated PDF content
            with open(file_path, 'wb') as f:
                f.write(sample_report_content)
            
            simulated_files.append(file_path)
            
            # Add small delay between files
            await asyncio.sleep(0.1)
        
        logger.info(f"Created {count} simulated radiology report files")
        return simulated_files
