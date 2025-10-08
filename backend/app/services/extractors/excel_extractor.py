"""
Excel/CSV Extractor Service
Extracts structured data from Excel and CSV files using pandas.
"""
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
from .base_extractor import BaseExtractor, ExtractionResult


class ExcelExtractor(BaseExtractor):
    """Extract structured data from Excel and CSV files"""
    
    # Supported file types
    SUPPORTED_MIMETYPES = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "application/csv"
    ]
    SUPPORTED_EXTENSIONS = [".xlsx", ".xls", ".csv"]
    
    def __init__(self):
        super().__init__()
    
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract data from Excel or CSV file
        
        Args:
            file_path: Path to Excel/CSV file
            
        Returns:
            ExtractionResult with extracted data
        """
        try:
            # Read file based on extension
            extension = file_path.suffix.lower()
            
            if extension == '.csv':
                df = self._read_csv(file_path)
            elif extension in ['.xlsx', '.xls']:
                df = self._read_excel(file_path)
            else:
                return ExtractionResult(
                    success=False,
                    error=f"Unsupported file extension: {extension}"
                )
            
            # Convert to text representation
            raw_text = self._dataframe_to_text(df)
            
            # Build structured data
            structured_data = self._dataframe_to_structured(df, file_path)
            
            # Extract metadata
            metadata = self._extract_metadata(df, file_path)
            
            return ExtractionResult(
                success=True,
                raw_text=raw_text,
                structured_data=structured_data,
                metadata=metadata
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error=f"Excel/CSV extraction failed: {str(e)}"
            )
    
    def _read_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Read CSV file with various encoding attempts
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            pandas DataFrame
        """
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if encoding == encodings[-1]:  # Last attempt
                    raise e
        
        raise Exception("Could not read CSV with any supported encoding")
    
    def _read_excel(self, file_path: Path) -> pd.DataFrame:
        """
        Read Excel file (supports .xlsx and .xls)
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            pandas DataFrame
        """
        # Read Excel file (first sheet by default)
        df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl' if file_path.suffix == '.xlsx' else None)
        return df
    
    def _dataframe_to_text(self, df: pd.DataFrame) -> str:
        """
        Convert DataFrame to readable text
        
        Args:
            df: pandas DataFrame
            
        Returns:
            Text representation
        """
        # Use pandas to_string for formatted output
        text = df.to_string(index=False, max_rows=1000)
        return text
    
    def _dataframe_to_structured(self, df: pd.DataFrame, file_path: Path) -> Dict:
        """
        Convert DataFrame to structured dictionary
        
        Args:
            df: pandas DataFrame
            file_path: Path to file
            
        Returns:
            Structured data dictionary
        """
        # Convert pandas Timestamps to ISO strings and handle NaN values for JSON serialization
        df_copy = df.copy()
        
        # First, replace NaN values with None for JSON compatibility
        df_copy = df_copy.replace({np.nan: None, pd.NA: None, pd.NaT: None})
        
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                # Convert datetime columns to ISO format strings
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
            elif hasattr(df_copy[col], 'dtype') and df_copy[col].dtype == 'object':
                # Handle any remaining pandas Timestamp objects, but preserve None values
                df_copy[col] = df_copy[col].apply(
                    lambda x: x.isoformat() if hasattr(x, 'isoformat') and x is not None else (str(x) if x is not None else None)
                )
        
        # Get column info
        columns = df_copy.columns.tolist()
        column_types = {col: str(df_copy[col].dtype) for col in columns}
        
        # Convert to list of dictionaries (records)
        records = df_copy.to_dict('records')
        
        # Detect potential transaction columns
        transaction_columns = self._detect_transaction_columns(columns)
        
        structured_data = {
            "file_type": file_path.suffix.lower(),
            "row_count": len(df_copy),
            "column_count": len(columns),
            "columns": columns,
            "column_types": column_types,
            "records": records,
            "detected_transaction_columns": transaction_columns,
            "is_likely_expense_sheet": bool(transaction_columns.get("amount") or transaction_columns.get("date"))
        }
        
        return structured_data
    
    def _detect_transaction_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Detect which columns might contain transaction data
        
        Args:
            columns: List of column names
            
        Returns:
            Dictionary mapping field types to column names
        """
        detected = {}
        
        # Convert to lowercase for matching
        columns_lower = {col.lower(): col for col in columns}
        
        # Date column patterns
        date_patterns = ['date', 'transaction_date', 'trans_date', 'datetime', 'timestamp']
        for pattern in date_patterns:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected['date'] = col_original
                    break
            if 'date' in detected:
                break
        
        # Amount column patterns
        amount_patterns = ['amount', 'total', 'price', 'cost', 'value', 'sum']
        for pattern in amount_patterns:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected['amount'] = col_original
                    break
            if 'amount' in detected:
                break
        
        # Vendor/Merchant column patterns
        vendor_patterns = ['vendor', 'merchant', 'supplier', 'company', 'store', 'payee']
        for pattern in vendor_patterns:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected['vendor'] = col_original
                    break
            if 'vendor' in detected:
                break
        
        # Description column patterns
        desc_patterns = ['description', 'memo', 'note', 'details', 'comment']
        for pattern in desc_patterns:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected['description'] = col_original
                    break
            if 'description' in detected:
                break
        
        # Category column patterns
        category_patterns = ['category', 'type', 'class', 'classification']
        for pattern in category_patterns:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected['category'] = col_original
                    break
            if 'category' in detected:
                break
        
        return detected
    
    def _extract_metadata(self, df: pd.DataFrame, file_path: Path) -> Dict:
        """
        Extract file metadata
        
        Args:
            df: pandas DataFrame
            file_path: Path to file
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix.lower(),
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "has_null_values": df.isnull().any().any(),
            "null_count": int(df.isnull().sum().sum())
        }
        
        return metadata
