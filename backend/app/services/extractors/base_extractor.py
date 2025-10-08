"""
Base Extractor Abstract Class
All document extractors (PDF, Image, Excel) inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from pathlib import Path
import mimetypes


class ExtractionResult:
    """Standardized result from document extraction"""
    
    def __init__(
        self,
        success: bool,
        raw_text: str = "",
        structured_data: Optional[Dict] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.success = success
        self.raw_text = raw_text
        self.structured_data = structured_data or {}
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "raw_text": self.raw_text,
            "structured_data": self.structured_data,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseExtractor(ABC):
    """Abstract base class for all document extractors"""
    
    # Supported MIME types for this extractor (override in subclasses)
    SUPPORTED_MIMETYPES: List[str] = []
    
    # Supported file extensions (override in subclasses)
    SUPPORTED_EXTENSIONS: List[str] = []
    
    def __init__(self):
        """Initialize extractor"""
        self.name = self.__class__.__name__
    
    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract text and data from document
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ExtractionResult with extracted data
        """
        pass
    
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle the given file
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if this extractor supports the file type
        """
        # Check by extension
        extension = file_path.suffix.lower()
        if extension in self.SUPPORTED_EXTENSIONS:
            return True
        
        # Check by MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type in self.SUPPORTED_MIMETYPES:
            return True
        
        return False
    
    def validate_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate file before extraction
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Check if it's a file (not directory)
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Try reading first byte
        except PermissionError:
            return False, f"Permission denied: {file_path}"
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"
        
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_path.stat().st_size > max_size:
            return False, f"File too large (max 50MB): {file_path}"
        
        # Check if empty
        if file_path.stat().st_size == 0:
            return False, f"File is empty: {file_path}"
        
        # Check if this extractor can handle the file
        if not self.can_handle(file_path):
            return False, f"Unsupported file type for {self.name}: {file_path.suffix}"
        
        return True, None
    
    def extract_safe(self, file_path: Path) -> ExtractionResult:
        """
        Safe extraction with validation and error handling
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ExtractionResult with extracted data or error
        """
        # Validate file first
        is_valid, error = self.validate_file(file_path)
        if not is_valid:
            return ExtractionResult(success=False, error=error)
        
        # Attempt extraction
        try:
            result = self.extract(file_path)
            return result
        except Exception as e:
            return ExtractionResult(
                success=False,
                error=f"{self.name} extraction failed: {str(e)}"
            )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Join with single newline
        cleaned = '\n'.join(lines)
        
        return cleaned
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.name}(extensions={self.SUPPORTED_EXTENSIONS})"
