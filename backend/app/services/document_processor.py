"""
Document Processor Service
Main orchestrator that routes documents to appropriate extractors
and manages the document processing pipeline.
"""
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import uuid

from .extractors import (
    BaseExtractor,
    ExtractionResult,
    PDFExtractor,
    ImageExtractor,
    ExcelExtractor
)


class DocumentProcessor:
    """
    Main document processing orchestrator.
    Routes documents to appropriate extractors based on file type.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize DocumentProcessor with all extractors
        
        Args:
            tesseract_path: Optional path to Tesseract executable for OCR
        """
        # Initialize all extractors
        self.extractors: list[BaseExtractor] = [
            PDFExtractor(),
            ImageExtractor(tesseract_path=tesseract_path),
            ExcelExtractor()
        ]
        
        # Create extractor registry for quick lookup
        self.extractor_registry = self._build_extractor_registry()
    
    def _build_extractor_registry(self) -> Dict[str, BaseExtractor]:
        """
        Build a registry mapping file extensions to extractors
        
        Returns:
            Dictionary mapping extensions to extractors
        """
        registry = {}
        for extractor in self.extractors:
            for ext in extractor.SUPPORTED_EXTENSIONS:
                registry[ext] = extractor
        return registry
    
    def get_extractor_for_file(self, file_path: Path) -> Optional[BaseExtractor]:
        """
        Get the appropriate extractor for a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extractor instance or None if no extractor supports the file
        """
        extension = file_path.suffix.lower()
        
        # Try to find extractor by extension
        if extension in self.extractor_registry:
            return self.extractor_registry[extension]
        
        # Try each extractor's can_handle method
        for extractor in self.extractors:
            if extractor.can_handle(file_path):
                return extractor
        
        return None
    
    def process_document(
        self,
        file_path: Path,
        document_id: Optional[str] = None
    ) -> Dict:
        """
        Process a document and extract text/data
        
        Args:
            file_path: Path to the document file
            document_id: Optional document ID for tracking
            
        Returns:
            Processing result dictionary
        """
        processing_id = document_id or str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        result = {
            "processing_id": processing_id,
            "file_name": file_path.name,
            "file_path": str(file_path),
            "started_at": start_time.isoformat(),
            "status": "processing",
            "extraction_result": None,
            "error": None,
            "extractor_used": None,
            "processing_time_ms": None
        }
        
        try:
            # Check if file exists
            if not file_path.exists():
                result["status"] = "failed"
                result["error"] = f"File not found: {file_path}"
                return result
            
            # Get appropriate extractor
            extractor = self.get_extractor_for_file(file_path)
            
            if not extractor:
                result["status"] = "failed"
                result["error"] = f"No extractor available for file type: {file_path.suffix}"
                return result
            
            result["extractor_used"] = extractor.name
            
            # Extract content
            extraction_result = extractor.extract_safe(file_path)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            result["processing_time_ms"] = round(processing_time, 2)
            result["completed_at"] = end_time.isoformat()
            
            # Update result
            if extraction_result.success:
                result["status"] = "completed"
                result["extraction_result"] = {
                    "raw_text": extraction_result.raw_text,
                    "structured_data": extraction_result.structured_data,
                    "metadata": extraction_result.metadata,
                    "text_length": len(extraction_result.raw_text),
                    "word_count": len(extraction_result.raw_text.split())
                }
            else:
                result["status"] = "failed"
                result["error"] = extraction_result.error
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            result["status"] = "failed"
            result["error"] = f"Processing exception: {str(e)}"
            result["processing_time_ms"] = round(processing_time, 2)
            result["completed_at"] = end_time.isoformat()
            
            return result
    
    def get_supported_extensions(self) -> list[str]:
        """
        Get list of all supported file extensions
        
        Returns:
            List of supported extensions (e.g., ['.pdf', '.png', '.xlsx'])
        """
        extensions = set()
        for extractor in self.extractors:
            extensions.update(extractor.SUPPORTED_EXTENSIONS)
        return sorted(list(extensions))
    
    def get_supported_mimetypes(self) -> list[str]:
        """
        Get list of all supported MIME types
        
        Returns:
            List of supported MIME types
        """
        mimetypes = set()
        for extractor in self.extractors:
            mimetypes.update(extractor.SUPPORTED_MIMETYPES)
        return sorted(list(mimetypes))
    
    def validate_file_type(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Check if a file type is supported
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_supported, error_message)
        """
        extractor = self.get_extractor_for_file(file_path)
        
        if extractor:
            return True, None
        else:
            supported_exts = ", ".join(self.get_supported_extensions())
            return False, f"Unsupported file type: {file_path.suffix}. Supported: {supported_exts}"
    
    def get_extractor_info(self) -> list[Dict]:
        """
        Get information about all available extractors
        
        Returns:
            List of extractor information dictionaries
        """
        info = []
        for extractor in self.extractors:
            info.append({
                "name": extractor.name,
                "supported_extensions": extractor.SUPPORTED_EXTENSIONS,
                "supported_mimetypes": extractor.SUPPORTED_MIMETYPES
            })
        return info
