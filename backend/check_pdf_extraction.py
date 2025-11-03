"""
Simple test to check PDF extraction status
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_processor import DocumentProcessor
from loguru import logger

def check_pdf():
    """Check if PDF can be extracted"""
    
    file_path = Path(r"C:\Users\Z C\Desktop\AgenticfiAI\multitransaction.pdf")
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return
    
    logger.info(f"Checking PDF: {file_path.name}")
    logger.info(f"File size: {file_path.stat().st_size / 1024:.2f} KB")
    
    # Try with DocumentProcessor
    processor = DocumentProcessor()
    
    logger.info("\nAttempting extraction...")
    result = processor.process_document(file_path)
    
    logger.info(f"\nExtraction result:")
    logger.info(f"  Success: {result.get('success')}")
    logger.info(f"  Raw text length: {len(result.get('raw_text', ''))}")
    logger.info(f"  Error: {result.get('error')}")
    logger.info(f"  Document type: {result.get('document_type')}")
    
    if result.get('raw_text'):
        logger.info(f"\nPreview (first 500 chars):")
        logger.info(result['raw_text'][:500])
    else:
        logger.warning("\n⚠️ No text extracted!")
        logger.warning("This PDF likely contains scanned images and requires OCR (Tesseract)")
        logger.warning("Please install Tesseract OCR and configure the path")

if __name__ == "__main__":
    check_pdf()
