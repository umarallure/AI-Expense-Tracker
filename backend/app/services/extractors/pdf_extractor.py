"""
PDF Extractor Service
Extracts text and tables from PDF documents using PyPDF2 and pdfplumber.
"""
from pathlib import Path
from typing import Dict, List
import PyPDF2
import pdfplumber
from .base_extractor import BaseExtractor, ExtractionResult


class PDFExtractor(BaseExtractor):
    """Extract text and structured data from PDF documents"""
    
    # Supported file types
    SUPPORTED_MIMETYPES = ["application/pdf"]
    SUPPORTED_EXTENSIONS = [".pdf"]
    
    def __init__(self):
        super().__init__()
    
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract text and tables from PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ExtractionResult with extracted text and tables
        """
        try:
            # Extract text using PyPDF2 (faster, but less accurate)
            text_pypdf2 = self._extract_text_pypdf2(file_path)
            
            # Extract text and tables using pdfplumber (more accurate)
            text_pdfplumber, tables = self._extract_with_pdfplumber(file_path)
            
            # Use pdfplumber text if available, fallback to PyPDF2
            raw_text = text_pdfplumber if text_pdfplumber.strip() else text_pypdf2
            
            # Clean the extracted text
            cleaned_text = self._clean_text(raw_text)
            
            # Build metadata
            metadata = self._extract_metadata(file_path)
            
            # Build structured data
            structured_data = {
                "page_count": metadata.get("page_count", 0),
                "has_tables": len(tables) > 0,
                "table_count": len(tables),
                "tables": tables,
                "extraction_method": "pdfplumber" if text_pdfplumber.strip() else "pypdf2"
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
                error=f"PDF extraction failed: {str(e)}"
            )
    
    def _extract_text_pypdf2(self, file_path: Path) -> str:
        """
        Extract text using PyPDF2 (fast but basic)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        except Exception as e:
            # Log error but don't fail, pdfplumber will be tried next
            print(f"PyPDF2 extraction warning: {str(e)}")
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pdfplumber(self, file_path: Path) -> tuple[str, List[Dict]]:
        """
        Extract text and tables using pdfplumber (more accurate)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, tables_list)
        """
        text_parts = []
        all_tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {page_num} ---\n{text}")
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        for table_idx, table in enumerate(tables):
                            # Convert table to structured format
                            table_data = self._format_table(table, page_num, table_idx + 1)
                            all_tables.append(table_data)
                            
                            # Add table to text representation
                            table_text = self._table_to_text(table)
                            text_parts.append(f"\n[Table {table_idx + 1} on Page {page_num}]\n{table_text}")
        
        except Exception as e:
            # Log error but don't fail
            print(f"pdfplumber extraction warning: {str(e)}")
        
        return "\n\n".join(text_parts), all_tables
    
    def _format_table(self, table: List[List[str]], page_num: int, table_num: int) -> Dict:
        """
        Format table data into structured format
        
        Args:
            table: Raw table data from pdfplumber
            page_num: Page number
            table_num: Table number on the page
            
        Returns:
            Formatted table dictionary
        """
        if not table or len(table) < 2:
            return {
                "page": page_num,
                "table_number": table_num,
                "headers": [],
                "rows": []
            }
        
        # First row is usually headers
        headers = [str(cell or "").strip() for cell in table[0]]
        
        # Remaining rows are data
        rows = []
        for row in table[1:]:
            row_data = [str(cell or "").strip() for cell in row]
            rows.append(row_data)
        
        return {
            "page": page_num,
            "table_number": table_num,
            "headers": headers,
            "rows": rows,
            "row_count": len(rows)
        }
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """
        Convert table to text representation
        
        Args:
            table: Raw table data
            
        Returns:
            Text representation of table
        """
        if not table:
            return ""
        
        text_lines = []
        for row in table:
            row_text = " | ".join([str(cell or "").strip() for cell in row])
            text_lines.append(row_text)
        
        return "\n".join(text_lines)
    
    def _extract_metadata(self, file_path: Path) -> Dict:
        """
        Extract PDF metadata
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "page_count": 0,
            "pdf_version": None,
            "author": None,
            "title": None,
            "subject": None,
            "creator": None,
            "creation_date": None
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Page count
                metadata["page_count"] = len(pdf_reader.pages)
                
                # PDF metadata
                if pdf_reader.metadata:
                    metadata["author"] = pdf_reader.metadata.get("/Author", None)
                    metadata["title"] = pdf_reader.metadata.get("/Title", None)
                    metadata["subject"] = pdf_reader.metadata.get("/Subject", None)
                    metadata["creator"] = pdf_reader.metadata.get("/Creator", None)
                    
                    # Creation date
                    creation_date = pdf_reader.metadata.get("/CreationDate", None)
                    if creation_date:
                        metadata["creation_date"] = str(creation_date)
        
        except Exception as e:
            print(f"Metadata extraction warning: {str(e)}")
        
        return metadata
