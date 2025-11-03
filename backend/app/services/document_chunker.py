"""
Document Chunker Service
Splits large documents into manageable chunks for processing.
Handles page-wise and size-based chunking strategies.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from loguru import logger


class DocumentChunker:
    """
    Splits large documents into chunks for efficient processing.
    Supports multiple chunking strategies based on document type and size.
    """
    
    def __init__(
        self,
        max_chunk_size: int = 8000,  # Max characters per chunk
        overlap_size: int = 200,      # Character overlap between chunks
        max_transactions_per_chunk: int = 50  # Max transactions per chunk
    ):
        """
        Initialize DocumentChunker with configuration
        
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap_size: Overlap between chunks to avoid splitting transactions
            max_transactions_per_chunk: Maximum transactions to process in one chunk
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.max_transactions_per_chunk = max_transactions_per_chunk
    
    def should_chunk_document(self, text: str, structured_data: Optional[Dict] = None) -> bool:
        """
        Determine if document should be chunked
        
        Args:
            text: Document text
            structured_data: Optional structured data
            
        Returns:
            True if document should be chunked
        """
        # Chunk if text is too large
        if len(text) > self.max_chunk_size * 2:
            return True
        
        # Chunk if too many transactions detected
        if structured_data:
            transactions = structured_data.get("transactions", [])
            if len(transactions) > self.max_transactions_per_chunk:
                return True
        
        return False
    
    def chunk_by_pages(self, text: str) -> List[Dict[str, Any]]:
        """
        Split document by pages (for PDFs with page markers)
        
        Args:
            text: Document text with page markers
            
        Returns:
            List of page chunks with metadata
        """
        chunks = []
        
        # Split by page markers (commonly "--- Page N ---")
        page_pattern = r'---\s*Page\s+(\d+)\s*---'
        pages = re.split(page_pattern, text)
        
        # Process pages (pattern: [text_before, page_num, page_content, page_num, page_content, ...]
        if len(pages) > 1:
            # First element is text before first page marker
            if pages[0].strip():
                chunks.append({
                    "chunk_id": 0,
                    "chunk_type": "page",
                    "page_number": 0,
                    "text": pages[0].strip(),
                    "char_count": len(pages[0])
                })
            
            # Process remaining pages
            for i in range(1, len(pages), 2):
                if i + 1 < len(pages):
                    page_num = int(pages[i])
                    page_content = pages[i + 1]
                    
                    if page_content.strip():
                        chunks.append({
                            "chunk_id": page_num,
                            "chunk_type": "page",
                            "page_number": page_num,
                            "text": page_content.strip(),
                            "char_count": len(page_content)
                        })
        else:
            # No page markers found, return as single chunk
            chunks.append({
                "chunk_id": 1,
                "chunk_type": "page",
                "page_number": 1,
                "text": text.strip(),
                "char_count": len(text)
            })
        
        logger.info(f"Split document into {len(chunks)} page chunks")
        return chunks
    
    def chunk_by_transactions(self, structured_data: Dict) -> List[Dict[str, Any]]:
        """
        Split by transaction groups (for structured data)
        
        Args:
            structured_data: Structured data with transactions array
            
        Returns:
            List of transaction chunks
        """
        chunks = []
        transactions = structured_data.get("transactions", [])
        
        if not transactions:
            return chunks
        
        # Split into batches
        for i in range(0, len(transactions), self.max_transactions_per_chunk):
            batch = transactions[i:i + self.max_transactions_per_chunk]
            
            chunks.append({
                "chunk_id": i // self.max_transactions_per_chunk + 1,
                "chunk_type": "transaction_batch",
                "transaction_count": len(batch),
                "start_index": i,
                "end_index": i + len(batch) - 1,
                "transactions": batch
            })
        
        logger.info(f"Split {len(transactions)} transactions into {len(chunks)} chunks")
        return chunks
    
    def chunk_by_size(self, text: str) -> List[Dict[str, Any]]:
        """
        Split document by size with smart boundaries
        
        Args:
            text: Document text
            
        Returns:
            List of text chunks with overlap
        """
        chunks = []
        text_length = len(text)
        
        if text_length <= self.max_chunk_size:
            return [{
                "chunk_id": 1,
                "chunk_type": "size",
                "text": text,
                "char_count": text_length,
                "start_pos": 0,
                "end_pos": text_length
            }]
        
        # Split by size with overlap
        start_pos = 0
        chunk_id = 1
        max_chunks = 1000  # Safety limit to prevent memory issues
        
        while start_pos < text_length and chunk_id <= max_chunks:
            # Calculate end position
            end_pos = min(start_pos + self.max_chunk_size, text_length)
            
            # Try to find a good breaking point (newline or sentence)
            if end_pos < text_length:
                # Look for newline within last 500 chars
                search_start = max(end_pos - 500, start_pos)
                last_newline = text.rfind('\n', search_start, end_pos)
                
                if last_newline > start_pos:
                    end_pos = last_newline + 1
                else:
                    # Look for period + space
                    last_sentence = text.rfind('. ', search_start, end_pos)
                    if last_sentence > start_pos:
                        end_pos = last_sentence + 2
            
            chunk_text = text[start_pos:end_pos]
            
            chunks.append({
                "chunk_id": chunk_id,
                "chunk_type": "size",
                "text": chunk_text.strip(),
                "char_count": len(chunk_text),
                "start_pos": start_pos,
                "end_pos": end_pos
            })
            
            # Move to next chunk with overlap, ensuring we always advance
            if end_pos - start_pos <= self.overlap_size:
                # If chunk is smaller than overlap, just move to end_pos
                start_pos = end_pos
            else:
                # Normal overlap
                start_pos = end_pos - self.overlap_size
            
            chunk_id += 1
            
            # Safety check
            if chunk_id > max_chunks:
                logger.warning(f"Reached maximum chunk limit ({max_chunks}), stopping chunking")
                break
        
        logger.info(f"Split document into {len(chunks)} size-based chunks")
        return chunks
    
    def chunk_document(
        self,
        text: str,
        structured_data: Optional[Dict] = None,
        strategy: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Chunk document using appropriate strategy
        
        Args:
            text: Document text
            structured_data: Optional structured data
            strategy: Chunking strategy ("auto", "pages", "transactions", "size")
            
        Returns:
            List of chunks with metadata
        """
        # Check if chunking is needed
        if not self.should_chunk_document(text, structured_data):
            logger.info("Document is small enough, no chunking needed")
            return [{
                "chunk_id": 1,
                "chunk_type": "full_document",
                "text": text,
                "char_count": len(text),
                "structured_data": structured_data
            }]
        
        # Auto-detect strategy
        if strategy == "auto":
            # Prefer transactions if available
            if structured_data and structured_data.get("transactions"):
                strategy = "transactions"
            # Then try pages
            elif "--- Page" in text:
                strategy = "pages"
            # Fall back to size-based
            else:
                strategy = "size"
        
        # Apply strategy
        if strategy == "transactions":
            return self.chunk_by_transactions(structured_data)
        elif strategy == "pages":
            return self.chunk_by_pages(text)
        elif strategy == "size":
            return self.chunk_by_size(text)
        else:
            logger.warning(f"Unknown strategy: {strategy}, using size-based")
            return self.chunk_by_size(text)
    
    def estimate_processing_time(self, chunks: List[Dict[str, Any]]) -> float:
        """
        Estimate total processing time for chunks
        
        Args:
            chunks: List of chunks
            
        Returns:
            Estimated time in seconds
        """
        # Rough estimates:
        # - 2 seconds per page chunk
        # - 5 seconds per 10 transactions
        # - 3 seconds per size chunk
        
        total_time = 0
        for chunk in chunks:
            chunk_type = chunk.get("chunk_type")
            
            if chunk_type == "page":
                total_time += 2
            elif chunk_type == "transaction_batch":
                tx_count = chunk.get("transaction_count", 0)
                total_time += (tx_count / 10) * 5
            elif chunk_type == "size":
                total_time += 3
            else:
                total_time += 2
        
        return total_time
