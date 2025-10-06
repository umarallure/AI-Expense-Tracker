from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.transaction import TransactionReport
from app.services.report_generator import ReportGenerator

router = APIRouter()
report_generator = ReportGenerator()

@router.get("/reports/income-statement", response_model=TransactionReport)
async def generate_income_statement(business_id: str, year: int):
    try:
        report = await report_generator.generate_income_statement(business_id, year)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/cash-flow", response_model=TransactionReport)
async def generate_cash_flow_statement(business_id: str, year: int):
    try:
        report = await report_generator.generate_cashflow_statement(business_id, year)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/tax", response_model=TransactionReport)
async def generate_tax_report(business_id: str, year: int):
    try:
        report = await report_generator.generate_tax_report(business_id, year)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))