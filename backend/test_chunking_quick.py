"""
Quick Chunking Test - No AI calls
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.document_chunker import DocumentChunker
from app.services.extractors.pdf_extractor import PDFExtractor
from loguru import logger


def test_chunking():
    """Test chunking logic without AI"""
    logger.info("=" * 80)
    logger.info("Quick Chunking Test")
    logger.info("=" * 80)
    
    # Test PDF
    pdf_path = Path("C:/Users/Z C/Desktop/AgenticfiAI/multitransaction.pdf")
    
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return
    
    logger.info(f"Processing: {pdf_path.name}")
    logger.info(f"File size: {pdf_path.stat().st_size / 1024:.2f} KB")
    
    # Extract text
    pdf_extractor = PDFExtractor()
    logger.info("Extracting text...")
    extraction_result = pdf_extractor.extract(Path(pdf_path))
    
    if not extraction_result.success:
        logger.error(f"Extraction failed: {extraction_result.error}")
        return
    
    raw_text = extraction_result.raw_text
    
    logger.info(f"✅ Extracted {len(raw_text)} characters")
    logger.info(f"Preview: {raw_text[:150]}...")
    
    # Test chunking
    # Initialize chunker with smaller chunk size for testing
    chunker = DocumentChunker(max_chunk_size=5000, max_transactions_per_chunk=50)
    
    should_chunk = chunker.should_chunk_document(raw_text)
    logger.info(f"\nShould chunk: {should_chunk}")
    
    if should_chunk:
        logger.info("Creating chunks...")
        chunks = chunker.chunk_by_size(raw_text)
        
        logger.info(f"✅ Created {len(chunks)} chunks")
        
        # Show chunk details
        total_chars = sum(c['char_count'] for c in chunks)
        avg_chars = total_chars / len(chunks)
        
        logger.info(f"\nChunk statistics:")
        logger.info(f"  Total characters: {total_chars:,}")
        logger.info(f"  Average chunk size: {avg_chars:.0f} chars")
        logger.info(f"  Min chunk size: {min(c['char_count'] for c in chunks):,} chars")
        logger.info(f"  Max chunk size: {max(c['char_count'] for c in chunks):,} chars")
        
        # Show first 3 chunks
        logger.info("\nFirst 3 chunks:")
        for i, chunk in enumerate(chunks[:3]):
            logger.info(
                f"\nChunk {i+1}:"
                f"\n  ID: {chunk['chunk_id']}"
                f"\n  Size: {chunk['char_count']:,} chars"
                f"\n  Preview: {chunk['text'][:100]}..."
            )
        
        # Estimate processing
        import re
        date_pattern = r'\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b'
        amount_pattern = r'[\$£€]\s*[\d,]+\.\d{2}|-\s*\$\s*[\d,]+\.\d{2}'
        
        lines = raw_text.split('\n')
        transaction_count = sum(
            1 for line in lines 
            if re.search(date_pattern, line) and re.search(amount_pattern, line)
        )
        
        logger.info(f"\nDetected ~{transaction_count} transaction patterns")
        
        estimated_time = chunker.estimate_processing_time(chunks)
        logger.info(f"Estimated processing time: {estimated_time:.1f}s ({estimated_time/60:.1f} min)")
        
        logger.info("\n✅ Chunking test successful!")
        logger.info(f"💡 This document would be split into {len(chunks)} API calls")
        logger.info(f"💡 Each call would process ~{avg_chars:.0f} characters")
        
    else:
        logger.info("Document does not need chunking (small enough)")


if __name__ == "__main__":
    test_chunking()
