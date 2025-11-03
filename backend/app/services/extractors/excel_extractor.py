"""
Excel/CSV Extractor Service
Extracts structured data from Excel and CSV files using pandas.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
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
            
            # Check if this looks like a multi-transaction document
            is_multi_transaction = self._is_multi_transaction_document(df)
            
            if is_multi_transaction:
                # Extract multiple transactions
                structured_data = self._extract_multiple_transactions(df, file_path)
            else:
                # Single transaction document (legacy behavior)
                structured_data = self._dataframe_to_structured(df, file_path)
            
            # Extract metadata
            metadata = self._extract_metadata(df, file_path)
            metadata["is_multi_transaction"] = is_multi_transaction
            
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
    
    def _is_multi_transaction_document(self, df: pd.DataFrame) -> bool:
        """
        Determine if this document contains multiple transactions
        
        Args:
            df: pandas DataFrame
            
        Returns:
            True if document appears to contain multiple transactions
        """
        if len(df) < 2:
            return False
        
        # Check for transaction indicators
        columns_lower = [col.lower() for col in df.columns]
        
        # Look for multiple rows with transaction-like data
        transaction_indicators = [
            'date', 'amount', 'transaction', 'vendor', 'merchant', 
            'description', 'debit', 'credit', 'balance'
        ]
        
        # Count how many transaction columns we have
        transaction_column_count = sum(
            1 for indicator in transaction_indicators 
            for col in columns_lower 
            if indicator in col
        )
        
        # If we have multiple transaction columns and multiple rows, likely multi-transaction
        if transaction_column_count >= 2 and len(df) >= 3:
            return True
        
        # Check for patterns that indicate bank statements or transaction lists
        # Look for sequential dates or amounts
        date_col = self._find_column_by_patterns(df, ['date', 'transaction_date'])
        amount_col = self._find_column_by_patterns(df, ['amount', 'debit', 'credit'])
        
        if date_col and amount_col:
            # Check if we have multiple valid dates and amounts
            valid_dates = df[date_col].notna().sum()
            valid_amounts = df[amount_col].notna().sum()
            
            # If more than 60% of rows have both date and amount, likely multi-transaction
            if valid_dates >= 3 and valid_amounts >= 3:
                valid_rows = ((df[date_col].notna()) & (df[amount_col].notna())).sum()
                if valid_rows / len(df) > 0.6:
                    return True
        
        return False
    
    def _extract_multiple_transactions(self, df: pd.DataFrame, file_path: Path) -> Dict:
        """
        Extract multiple transactions from DataFrame
        
        Args:
            df: pandas DataFrame
            file_path: Path to file
            
        Returns:
            Structured data with multiple transactions
        """
        # Detect transaction columns
        transaction_columns = self._detect_transaction_columns(df.columns.tolist())
        
        # Clean and prepare data
        df_clean = self._prepare_transaction_dataframe(df, transaction_columns)
        
        # Extract individual transactions
        transactions = []
        for idx, row in df_clean.iterrows():
            transaction = self._extract_single_transaction_from_row(row, transaction_columns)
            if transaction:
                transactions.append(transaction)
        
        # Build structured data
        structured_data = {
            "document_type": "multi_transaction_excel",
            "file_type": file_path.suffix.lower(),
            "total_rows": len(df),
            "transaction_rows": len(transactions),
            "detected_transaction_columns": transaction_columns,
            "transactions": transactions,
            "extraction_method": "multi_transaction",
            "is_likely_expense_sheet": True
        }
        
        return structured_data
    
    def _prepare_transaction_dataframe(self, df: pd.DataFrame, transaction_columns: Dict[str, str]) -> pd.DataFrame:
        """
        Prepare DataFrame for transaction extraction
        
        Args:
            df: Raw DataFrame
            transaction_columns: Mapping of field types to column names
            
        Returns:
            Cleaned DataFrame ready for transaction extraction
        """
        df_copy = df.copy()
        
        # Remove completely empty rows
        df_copy = df_copy.dropna(how='all')
        
        # Remove header-like rows (if they exist in data)
        if len(df_copy) > 1:
            # Check if first row looks like headers
            first_row = df_copy.iloc[0].astype(str).str.lower()
            potential_headers = ['date', 'amount', 'description', 'vendor', 'transaction']
            
            header_score = sum(1 for header in potential_headers if 
                             any(header in str(cell) for cell in first_row))
            
            # If first row looks like headers and we have a lot of rows, remove it
            if header_score >= 2 and len(df_copy) > 5:
                df_copy = df_copy.iloc[1:].reset_index(drop=True)
        
        # Clean amount columns
        if 'amount' in transaction_columns:
            amount_col = transaction_columns['amount']
            df_copy[amount_col] = df_copy[amount_col].apply(self._clean_amount_value)
        
        # Clean date columns
        if 'date' in transaction_columns:
            date_col = transaction_columns['date']
            df_copy[date_col] = df_copy[date_col].apply(self._clean_date_value)
        
        return df_copy
    
    def _extract_single_transaction_from_row(self, row: pd.Series, transaction_columns: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Extract a single transaction from a DataFrame row
        
        Args:
            row: pandas Series representing one row
            transaction_columns: Mapping of field types to column names
            
        Returns:
            Transaction dictionary or None if invalid
        """
        transaction = {}
        
        # Extract basic fields
        if 'date' in transaction_columns:
            date_val = row.get(transaction_columns['date'])
            if pd.notna(date_val):
                transaction['date'] = self._format_date_for_transaction(date_val)
        
        if 'amount' in transaction_columns:
            amount_val = row.get(transaction_columns['amount'])
            if pd.notna(amount_val):
                transaction['amount'] = self._format_amount_for_transaction(amount_val)
        
        if 'vendor' in transaction_columns:
            vendor_val = row.get(transaction_columns['vendor'])
            if pd.notna(vendor_val):
                transaction['vendor'] = str(vendor_val).strip()
        
        if 'description' in transaction_columns:
            desc_val = row.get(transaction_columns['description'])
            if pd.notna(desc_val):
                transaction['description'] = str(desc_val).strip()
        
        if 'category' in transaction_columns:
            cat_val = row.get(transaction_columns['category'])
            if pd.notna(cat_val):
                transaction['category'] = str(cat_val).strip()
        
        # Determine if it's income or expense
        if 'amount' in transaction and transaction['amount'] is not None:
            amount = transaction['amount']
            # Negative amounts are typically expenses, positive are income
            transaction['is_income'] = amount > 0
        
        # Only return transaction if it has minimum required fields
        required_fields = ['date', 'amount']
        has_required = all(field in transaction and transaction[field] is not None 
                          for field in required_fields)
        
        if has_required:
            # Add row metadata
            transaction['_row_index'] = row.name
            transaction['_extraction_method'] = 'excel_row'
            return transaction
        
        return None
    
    def _clean_amount_value(self, value: Any) -> Optional[float]:
        """Clean amount value for processing"""
        if pd.isna(value):
            return None
        
        try:
            # Convert to string and clean
            str_val = str(value).strip()
            
            # Remove currency symbols and commas
            str_val = str_val.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
            
            # Handle negative indicators
            if str_val.startswith('-'):
                str_val = str_val[1:]
                multiplier = -1
            else:
                multiplier = 1
            
            return float(str_val) * multiplier
            
        except (ValueError, TypeError):
            return None
    
    def _clean_date_value(self, value: Any) -> Optional[str]:
        """Clean date value for processing"""
        if pd.isna(value):
            return None
        
        try:
            # Try pandas date conversion
            if hasattr(value, 'date'):
                return value.date().isoformat()
            elif isinstance(value, str):
                # Try to parse string date
                parsed = pd.to_datetime(value, errors='coerce')
                if pd.notna(parsed):
                    return parsed.date().isoformat()
        except:
            pass
        
        return None
    
    def _format_date_for_transaction(self, date_val: Any) -> Optional[str]:
        """Format date for transaction storage"""
        if isinstance(date_val, str) and len(date_val) == 10:  # YYYY-MM-DD
            return date_val
        return None
    
    def _format_amount_for_transaction(self, amount_val: Any) -> Optional[float]:
        """Format amount for transaction storage"""
        if isinstance(amount_val, (int, float)):
            return float(amount_val)
        return None
    
    def _find_column_by_patterns(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        """
        Find column by pattern matching
        
        Args:
            df: DataFrame
            patterns: List of patterns to match
            
        Returns:
            Column name or None
        """
        columns_lower = {col: col.lower() for col in df.columns}
        
        for pattern in patterns:
            for col, col_lower in columns_lower.items():
                if pattern in col_lower:
                    return col
        
        return None
