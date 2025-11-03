"""
Complete End-to-End Test for Multi-Transaction Document Processing
Tests the entire pipeline from PDF extraction to transaction creation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from datetime import datetime
from loguru import logger
from supabase import create_client, Client
import os

# Import services
from app.services.document_processor import DocumentProcessor
from app.services.document_classifier import DocumentClassifier
from app.services.document_chunker import DocumentChunker
from app.services.ai.data_extractor import DataExtractor
from app.services.ai.confidence_scorer import ConfidenceScorer
from app.services.transaction_creator import TransactionCreator

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://klqumxsirbyqxqztlrfw.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

async def test_complete_pipeline():
    """Test the complete document processing pipeline"""
    
    logger.info("="*80)
    logger.info("Complete Multi-Transaction Pipeline Test")
    logger.info("="*80)
    
    # File path
    file_path = Path(r"C:\Users\Z C\Desktop\AgenticfiAI\multitransaction.pdf")
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return
    
    file_size = file_path.stat().st_size / 1024  # KB
    logger.info(f"\n📄 Processing: {file_path.name}")
    logger.info(f"📊 File size: {file_size:.2f} KB")
    
    # Initialize services
    logger.info("\n🔧 Initializing services...")
    document_processor = DocumentProcessor()
    classifier = DocumentClassifier()
    chunker = DocumentChunker(max_chunk_size=5000, max_transactions_per_chunk=50)
    data_extractor = DataExtractor()
    confidence_scorer = ConfidenceScorer()
    transaction_creator = TransactionCreator(confidence_threshold=0.85)
    
    # Initialize Supabase (optional - for full integration test)
    supabase_client = None
    if SUPABASE_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Supabase not available: {e}")
    
    # STEP 1: Extract text
    logger.info("\n" + "="*80)
    logger.info("STEP 1: Text Extraction")
    logger.info("="*80)
    start_time = datetime.now()
    
    # Use document processor which handles OCR
    processing_result = document_processor.process_document(file_path)
    raw_text = processing_result.get("raw_text", "")
    structured_data = processing_result.get("structured_data", {})
    
    extraction_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"✅ Extracted {len(raw_text)} characters in {extraction_time:.2f}s")
    logger.info(f"📝 Preview: {raw_text[:200]}...")
    
    # STEP 2: Classify document
    logger.info("\n" + "="*80)
    logger.info("STEP 2: Document Classification")
    logger.info("="*80)
    
    classification = classifier.classify_document(raw_text, str(file_path))
    logger.info(f"✅ Document type: {classification.document_type}")
    logger.info(f"📊 Confidence: {classification.confidence:.2f}")
    logger.info(f"🔄 Multi-transaction: {classification.is_multi_transaction}")
    
    # STEP 3: Check chunking need
    logger.info("\n" + "="*80)
    logger.info("STEP 3: Chunking Assessment")
    logger.info("="*80)
    
    should_chunk = chunker.should_chunk_document(raw_text, None)
    logger.info(f"Should chunk: {should_chunk}")
    
    if should_chunk:
        chunks = chunker.chunk_by_size(raw_text)
        logger.info(f"✅ Created {len(chunks)} chunks")
        
        # Stats
        total_chars = sum(c["char_count"] for c in chunks)
        avg_chars = total_chars / len(chunks) if chunks else 0
        logger.info(f"📊 Total characters: {total_chars:,}")
        logger.info(f"📊 Average chunk size: {avg_chars:.0f} chars")
        
        estimated_time = chunker.estimate_processing_time(chunks)
        logger.info(f"⏱️ Estimated processing time: {estimated_time:.1f}s ({estimated_time/60:.1f} min)")
    else:
        chunks = [{"chunk_id": 1, "text": raw_text, "char_count": len(raw_text)}]
        logger.info("Document is small enough, no chunking needed")
    
    # STEP 4: Process chunks with AI (limited to first 2 chunks for testing)
    logger.info("\n" + "="*80)
    logger.info("STEP 4: AI Extraction (Testing with first 2 chunks)")
    logger.info("="*80)
    
    all_extracted_data = []
    test_chunks = chunks[:2]  # Only process first 2 chunks for testing
    
    for idx, chunk in enumerate(test_chunks):
        logger.info(f"\n📦 Processing chunk {idx + 1}/{len(test_chunks)}...")
        logger.info(f"   Size: {chunk['char_count']} characters")
        
        start_time = datetime.now()
        
        # Extract data
        if supabase_client:
            # Use a test business_id - replace with actual ID
            test_business_id = "75e0a128-cafd-4244-9320-72570b4831c7"
            
            chunk_extracted = await data_extractor.extract(
                text=chunk["text"],
                document_type=classification.document_type,
                business_id=test_business_id,
                supabase_client=supabase_client
            )
        else:
            # Mock extraction result without Supabase
            chunk_extracted = {
                "extraction_type": "multi_transaction",
                "transactions": [],
                "message": "Skipped - no Supabase connection"
            }
            logger.warning("⚠️ Skipping AI extraction (no Supabase)")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Check results
        extraction_type = chunk_extracted.get("extraction_type", "unknown")
        transactions = chunk_extracted.get("transactions", [])
        
        logger.info(f"✅ Chunk {idx + 1} processed in {processing_time:.2f}s")
        logger.info(f"   Extraction type: {extraction_type}")
        logger.info(f"   Transactions found: {len(transactions)}")
        
        if transactions:
            all_extracted_data.extend(transactions)
            # Show first transaction
            first_tx = transactions[0]
            logger.info(f"   Sample: {first_tx.get('vendor', 'N/A')} - ${first_tx.get('amount', 0.0)}")
    
    # STEP 5: Calculate confidence scores
    logger.info("\n" + "="*80)
    logger.info("STEP 5: Confidence Scoring")
    logger.info("="*80)
    
    if all_extracted_data:
        combined_result = {
            "extraction_type": "multi_transaction",
            "transactions": all_extracted_data,
            "total_transactions_extracted": len(all_extracted_data)
        }
        
        confidence_result = confidence_scorer.calculate_confidence(combined_result)
        overall_confidence = confidence_result.get("overall_confidence", 0.0)
        
        logger.info(f"✅ Overall confidence: {overall_confidence:.2%}")
        logger.info(f"📊 Valid transactions: {len(all_extracted_data)}")
        
        # Show confidence breakdown
        if "transaction_confidences" in confidence_result:
            tx_confidences = confidence_result["transaction_confidences"]
            if tx_confidences:
                avg_conf = sum(tx_confidences) / len(tx_confidences)
                logger.info(f"📊 Average transaction confidence: {avg_conf:.2%}")
    else:
        logger.warning("⚠️ No transactions extracted")
        overall_confidence = 0.0
    
    # STEP 6: Transaction creation (simulated)
    logger.info("\n" + "="*80)
    logger.info("STEP 6: Transaction Creation (Simulated)")
    logger.info("="*80)
    
    if all_extracted_data and supabase_client:
        logger.info(f"Would create {len(all_extracted_data)} transaction records")
        
        # Check which would be auto-approved
        high_confidence_count = sum(
            1 for tx in all_extracted_data 
            if tx.get("field_confidence", {}).get("amount", 0) > 0.85
        )
        logger.info(f"📊 High confidence transactions: {high_confidence_count}")
        logger.info(f"📊 Would require review: {len(all_extracted_data) - high_confidence_count}")
    else:
        logger.info("⚠️ Skipping transaction creation (testing mode)")
    
    # STEP 7: Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"📄 Document: {file_path.name}")
    logger.info(f"📊 File size: {file_size:.2f} KB")
    logger.info(f"📝 Characters extracted: {len(raw_text):,}")
    logger.info(f"🔤 Document type: {classification.document_type}")
    logger.info(f"🔄 Multi-transaction: {classification.is_multi_transaction}")
    logger.info(f"📦 Chunks created: {len(chunks)}")
    logger.info(f"🧪 Chunks tested: {len(test_chunks)}")
    logger.info(f"💰 Transactions extracted: {len(all_extracted_data)}")
    logger.info(f"📊 Overall confidence: {overall_confidence:.2%}")
    
    if len(chunks) > len(test_chunks):
        logger.info(f"\n💡 Note: Only tested {len(test_chunks)}/{len(chunks)} chunks")
        logger.info(f"   Full processing would extract ~{len(all_extracted_data) * len(chunks) / len(test_chunks):.0f} transactions")
        logger.info(f"   Estimated total time: ~{estimated_time:.1f}s ({estimated_time/60:.1f} min)")
    
    logger.info("\n" + "="*80)
    logger.info("✅ Complete pipeline test finished successfully!")
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())
