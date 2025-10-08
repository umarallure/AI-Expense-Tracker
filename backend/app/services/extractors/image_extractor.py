"""
Image Extractor Service
Extracts text from images using Tesseract OCR with image preprocessing.
"""
from pathlib import Path
from typing import Dict, Optional
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from .base_extractor import BaseExtractor, ExtractionResult


class ImageExtractor(BaseExtractor):
    """Extract text from images using OCR"""
    
    # Supported file types
    SUPPORTED_MIMETYPES = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/gif",
        "image/bmp",
        "image/tiff"
    ]
    SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"]
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize ImageExtractor
        
        Args:
            tesseract_path: Optional path to Tesseract executable
                          (auto-detected if not provided)
        """
        super().__init__()
        
        # Set Tesseract path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Try common Windows installation path
            common_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
            if common_path.exists():
                pytesseract.pytesseract.tesseract_cmd = str(common_path)
    
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract text from image using OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            ExtractionResult with extracted text
        """
        try:
            # Verify Tesseract is available
            try:
                pytesseract.get_tesseract_version()
            except Exception as e:
                return ExtractionResult(
                    success=False,
                    error=f"Tesseract OCR not found. Please install Tesseract and add to PATH. Error: {str(e)}"
                )
            
            # Load image
            image = Image.open(file_path)
            
            # Get original metadata
            metadata = self._extract_metadata(image, file_path)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Extract text with Tesseract
            raw_text = pytesseract.image_to_string(processed_image, lang='eng')
            
            # Clean extracted text
            cleaned_text = self._clean_text(raw_text)
            
            # Get OCR confidence data
            ocr_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidence_score = self._calculate_confidence(ocr_data)
            
            # Build structured data
            structured_data = {
                "extraction_method": "tesseract_ocr",
                "language": "eng",
                "confidence_score": confidence_score,
                "word_count": len(cleaned_text.split()),
                "preprocessing_applied": True,
                "image_size": metadata.get("dimensions")
            }
            
            return ExtractionResult(
                success=True,
                raw_text=cleaned_text,
                structured_data=structured_data,
                metadata=metadata
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error=f"Image OCR extraction failed: {str(e)}"
            )
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed image
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small (min 300 DPI equivalent)
            width, height = image.size
            min_dimension = 1000
            if width < min_dimension or height < min_dimension:
                scale = max(min_dimension / width, min_dimension / height)
                new_size = (int(width * scale), int(height * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Apply threshold to create binary image
            threshold = 128
            image = image.point(lambda p: 255 if p > threshold else 0)
            
            return image
            
        except Exception as e:
            print(f"Image preprocessing warning: {str(e)}")
            # Return original if preprocessing fails
            return image
    
    def _calculate_confidence(self, ocr_data: Dict) -> float:
        """
        Calculate average OCR confidence from Tesseract data
        
        Args:
            ocr_data: OCR data dictionary from Tesseract
            
        Returns:
            Average confidence score (0-1)
        """
        try:
            confidences = [
                float(conf) 
                for conf in ocr_data.get('conf', []) 
                if conf != '-1'  # -1 means no confidence available
            ]
            
            if not confidences:
                return 0.0
            
            avg_confidence = sum(confidences) / len(confidences)
            # Normalize to 0-1 range (Tesseract returns 0-100)
            return round(avg_confidence / 100, 2)
            
        except Exception as e:
            print(f"Confidence calculation warning: {str(e)}")
            return 0.0
    
    def _extract_metadata(self, image: Image.Image, file_path: Path) -> Dict:
        """
        Extract image metadata
        
        Args:
            image: PIL Image object
            file_path: Path to image file
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "format": image.format,
            "mode": image.mode,
            "dimensions": f"{image.size[0]}x{image.size[1]}",
            "width": image.size[0],
            "height": image.size[1]
        }
        
        # Extract EXIF data if available
        try:
            exif = image._getexif()
            if exif:
                metadata["has_exif"] = True
                # Add common EXIF tags
                exif_tags = {
                    271: "make",
                    272: "model",
                    306: "datetime",
                    36867: "datetime_original",
                }
                for tag_id, tag_name in exif_tags.items():
                    if tag_id in exif:
                        metadata[tag_name] = str(exif[tag_id])
        except Exception:
            metadata["has_exif"] = False
        
        return metadata
