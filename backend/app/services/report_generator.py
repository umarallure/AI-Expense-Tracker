from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel
import pandas as pd

class Report(BaseModel):
    title: str
    generated_at: datetime
    data: Dict

class ReportGenerator:
    def generate_income_statement(self, transactions: List[Dict], filters: Dict) -> Report:
        filtered_data = self.filter_transactions(transactions, filters)
        total_income = sum(item['amount'] for item in filtered_data if item['type'] == 'income')
        total_expense = sum(item['amount'] for item in filtered_data if item['type'] == 'expense')
        
        report_data = {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_income": total_income - total_expense,
            "transactions": filtered_data
        }
        
        return Report(title="Income Statement", generated_at=datetime.now(), data=report_data)

    def generate_cashflow_statement(self, transactions: List[Dict], filters: Dict) -> Report:
        filtered_data = self.filter_transactions(transactions, filters)
        cash_inflow = sum(item['amount'] for item in filtered_data if item['type'] == 'income')
        cash_outflow = sum(item['amount'] for item in filtered_data if item['type'] == 'expense')
        
        report_data = {
            "cash_inflow": cash_inflow,
            "cash_outflow": cash_outflow,
            "net_cashflow": cash_inflow - cash_outflow,
            "transactions": filtered_data
        }
        
        return Report(title="Cash Flow Statement", generated_at=datetime.now(), data=report_data)

    def filter_transactions(self, transactions: List[Dict], filters: Dict) -> List[Dict]:
        df = pd.DataFrame(transactions)
        for key, value in filters.items():
            df = df[df[key] == value]
        return df.to_dict(orient='records')