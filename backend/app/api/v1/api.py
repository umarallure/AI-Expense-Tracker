"""
API v1 router configuration.
Includes all endpoint routers for the application.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, businesses, accounts, categories, transactions  # , documents, rules, reports

api_router = APIRouter()

# Phase 1: Authentication and Business Management
api_router.include_router(auth.router)
api_router.include_router(businesses.router)

# Phase 2: Account and Category Management
api_router.include_router(accounts.router)
api_router.include_router(categories.router)

# Phase 2+: To be uncommented as implemented
api_router.include_router(transactions.router)
# api_router.include_router(documents.router)
# api_router.include_router(rules.router)
# api_router.include_router(reports.router)