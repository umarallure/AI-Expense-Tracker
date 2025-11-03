"""
Test Chunked Multi-Transaction Processing
Tests the complete flow: PDF extraction -> Chunking -> AI extraction -> Transaction creation
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.document_chunker import DocumentChunker
from app.services.data_extractor import DataExtractor
from app.services.confidence_scorer import ConfidenceScorer
from app.extractors.pdf_extractor import PDFExtractor
from loguru import logger


async def test_chunking():
    """Test document chunking functionality"""
    logger.info("=" * 80)
    logger.info("Testing Document Chunking")
    logger.info("=" * 80)
    
    # Initialize services
    chunker = DocumentChunker(max_chunk_size=8000, max_transactions_per_chunk=50)
    
    # Simulate large document text (bank statement with multiple transactions)
    sample_transactions = []
    for i in range(150):  # 150 transactions
        sample_transactions.append(
            f"Date: 2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d} "
            f"Vendor-{i} ${100 + i * 10}.00 "
            f"Description: Transaction {i}"
        )
    
    raw_text = "\n".join(sample_transactions)
    
    # Test should_chunk_document
    should_chunk = chunker.should_chunk_document(raw_text)
    logger.info(f"Should chunk document: {should_chunk}")
    logger.info(f"Text length: {len(raw_text)} chars")
    logger.info(f"Transaction count: {len(sample_transactions)}")
    
    # Test chunk_by_size
    logger.info("\n--- Testing size-based chunking ---")
    chunks = chunker.chunk_by_size(raw_text)
    logger.info(f"Created {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        logger.info(
            f"Chunk {i}: ID={chunk['chunk_id']}, "
            f"Chars={chunk['char_count']}, "
            f"Preview={chunk['text'][:100]}..."
        )
    
    # Test estimate_processing_time
    estimated_time = chunker.estimate_processing_time(len(chunks), len(sample_transactions))
    logger.info(f"\nEstimated processing time: {estimated_time:.1f} seconds ({estimated_time/60:.1f} minutes)")
    
    return chunks, raw_text


async def test_pdf_with_chunking():
    """Test PDF extraction with chunking"""
    logger.info("\n" + "=" * 80)
    logger.info("Testing PDF Extraction with Chunking")
    logger.info("=" * 80)
    
    # Path to test PDF
    pdf_path = Path("C:/Users/Z C/Desktop/AgenticfiAI/multitransaction.pdf")
    
    if not pdf_path.exists():
        logger.error(f"Test PDF not found at {pdf_path}")
        return None
    
    logger.info(f"Processing: {pdf_path}")
    logger.info(f"File size: {pdf_path.stat().st_size / 1024:.2f} KB")
    
    # Extract text
    pdf_extractor = PDFExtractor()
    raw_text = pdf_extractor.extract(str(pdf_path))
    
    logger.info(f"Extracted {len(raw_text)} characters")
    logger.info(f"Preview: {raw_text[:200]}...")
    
    # Test chunking
    chunker = DocumentChunker(max_chunk_size=8000, max_transactions_per_chunk=50)
    
    should_chunk = chunker.should_chunk_document(raw_text)
    logger.info(f"\nShould chunk: {should_chunk}")
    
    if should_chunk:
        chunks = chunker.chunk_by_size(raw_text)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Show chunk distribution
        for i, chunk in enumerate(chunks[:5]):  # First 5 chunks
            logger.info(
                f"Chunk {i}: {chunk['char_count']} chars, "
                f"Preview: {chunk['text'][:80]}..."
            )
        
        # Estimate processing time
        # Detect transaction count (rough estimate)
        import re
        date_pattern = r'\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b'
        amount_pattern = r'[\$£€]\s*[\d,]+\.\d{2}|-\s*\$\s*[\d,]+\.\d{2}'
        
        # Count patterns that appear together (date + amount = likely transaction)
        lines = raw_text.split('\n')
        transaction_count = 0
        for line in lines:
            has_date = bool(re.search(date_pattern, line))
            has_amount = bool(re.search(amount_pattern, line))
            if has_date and has_amount:
                transaction_count += 1
        
        logger.info(f"\nDetected ~{transaction_count} transaction patterns")
        estimated_time = chunker.estimate_processing_time(len(chunks), transaction_count)
        logger.info(f"Estimated processing time: {estimated_time:.1f} seconds ({estimated_time/60:.1f} minutes)")
        
        return chunks, raw_text, transaction_count
    
    return None, raw_text, 0


async def test_ai_extraction_chunked():
    """Test AI extraction on chunked data"""
    logger.info("\n" + "=" * 80)
    logger.info("Testing AI Extraction on Chunks")
    logger.info("=" * 80)
    
    # Get chunks from PDF
    result = await test_pdf_with_chunking()
    if not result or result[0] is None:
        logger.warning("No chunks to process")
        return
    
    chunks, full_text, tx_count = result
    
    # Initialize services
    data_extractor = DataExtractor()
    confidence_scorer = ConfidenceScorer()
    
    # Process first chunk as a test
    logger.info("\n--- Processing first chunk with AI ---")
    first_chunk = chunks[0]
    
    logger.info(f"Chunk text length: {first_chunk['char_count']}")
    logger.info(f"Chunk preview: {first_chunk['text'][:200]}...")
    
    # Extract from chunk
    logger.info("\nCalling AI extraction...")
    extracted_data = await data_extractor.extract(
        document_type="bank_statement",
        raw_text=first_chunk['text'],
        user_id="test-user-123",
        business_id="test-business-123",
        file_path=None
    )
    
    if extracted_data:
        logger.info(f"\n✅ Extraction successful!")
        logger.info(f"Extraction type: {extracted_data.get('extraction_type')}")
        
        transactions = extracted_data.get("transactions", [])
        logger.info(f"Transactions extracted: {len(transactions)}")
        
        # Show first 3 transactions
        for i, tx in enumerate(transactions[:3]):
            logger.info(
                f"\nTransaction {i+1}:"
                f"\n  Vendor: {tx.get('vendor')}"
                f"\n  Amount: ${tx.get('amount')}"
                f"\n  Date: {tx.get('date')}"
                f"\n  Description: {tx.get('description', 'N/A')[:100]}"
            )
        
        # Calculate confidence
        confidence = confidence_scorer.calculate_confidence(extracted_data)
        logger.info(f"\nOverall confidence: {confidence:.2%}")
        
        return extracted_data
    else:
        logger.error("❌ Extraction failed")
        return None


async def test_full_integration():
    """Test the complete integration: Chunking -> Extraction -> Transaction Creation"""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Full Integration (WITHOUT Database)")
    logger.info("=" * 80)
    
    # Get chunks
    result = await test_pdf_with_chunking()
    if not result or result[0] is None:
        logger.warning("No chunks to process")
        return
    
    chunks, full_text, tx_count = result
    
    # Initialize services
    data_extractor = DataExtractor()
    confidence_scorer = ConfidenceScorer()
    
    # Process chunks (limit to first 3 for testing)
    test_chunks = chunks[:3]
    logger.info(f"\n--- Processing {len(test_chunks)} chunks (of {len(chunks)} total) ---")
    
    all_transactions = []
    
    for i, chunk in enumerate(test_chunks):
        logger.info(f"\nProcessing chunk {i+1}/{len(test_chunks)}...")
        
        # Extract
        extracted_data = await data_extractor.extract(
            document_type="bank_statement",
            raw_text=chunk['text'],
            user_id="test-user-123",
            business_id="test-business-123",
            file_path=None
        )
        
        if extracted_data and extracted_data.get("transactions"):
            transactions = extracted_data["transactions"]
            all_transactions.extend(transactions)
            logger.info(f"  ✅ Extracted {len(transactions)} transactions from chunk {i+1}")
        else:
            logger.warning(f"  ⚠️ No transactions extracted from chunk {i+1}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total chunks created: {len(chunks)}")
    logger.info(f"Chunks processed: {len(test_chunks)}")
    logger.info(f"Total transactions extracted: {len(all_transactions)}")
    logger.info(f"Estimated transactions in full document: {tx_count}")
    
    if all_transactions:
        # Show sample transactions
        logger.info("\n--- Sample Transactions ---")
        for i, tx in enumerate(all_transactions[:5]):
            logger.info(
                f"\n{i+1}. {tx.get('vendor', 'Unknown')} - ${tx.get('amount', 0):.2f}"
                f"\n   Date: {tx.get('date', 'Unknown')}"
                f"\n   Description: {tx.get('description', 'N/A')[:80]}..."
            )
        
        # Calculate confidence
        multi_tx_data = {
            "extraction_type": "multi_transaction",
            "transactions": all_transactions,
            "total_transactions": len(all_transactions)
        }
        
        overall_confidence = confidence_scorer.calculate_confidence(multi_tx_data)
        logger.info(f"\nOverall confidence: {overall_confidence:.2%}")
        
        # Estimate what would happen in production
        logger.info("\n--- Production Simulation ---")
        if len(chunks) > len(test_chunks):
            extrapolated_tx = int(len(all_transactions) * (len(chunks) / len(test_chunks)))
            logger.info(f"Extrapolated transactions for full document: ~{extrapolated_tx}")
        
        chunker = DocumentChunker()
        estimated_time = chunker.estimate_processing_time(len(chunks), tx_count)
        logger.info(f"Full document processing time: ~{estimated_time:.1f}s ({estimated_time/60:.1f} min)")
        
        logger.info("\n✅ Integration test successful!")
        logger.info("💡 Next step: Test with actual database to verify transaction creation")
    else:
        logger.error("❌ No transactions extracted")


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Chunked Multi-Transaction Processing Tests\n")
    
    try:
        # Test 1: Basic chunking
        await test_chunking()
        
        # Test 2: PDF extraction with chunking
        await test_pdf_with_chunking()
        
        # Test 3: AI extraction on chunks
        await test_ai_extraction_chunked()
        
        # Test 4: Full integration
        await test_full_integration()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL TESTS COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
