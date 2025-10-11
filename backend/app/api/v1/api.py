"""
API v1 router configuration.
Includes all endpoint routers for the application.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    businesses,
    accounts,
    categories,
    transactions,
    documents,
    document_processing,
    project_divisions
)  # , rules, reports

api_router = APIRouter()

# Phase 1: Authentication and Business Management
api_router.include_router(auth.router)
api_router.include_router(businesses.router)

# Phase 2: Account and Category Management
api_router.include_router(accounts.router)
api_router.include_router(categories.router)

# Project Divisions (Business Organization)
api_router.include_router(project_divisions.router)

# Phase 2+: Transaction and Document Management
api_router.include_router(transactions.router)
api_router.include_router(documents.router)

# Phase 3.2: Document Processing Pipeline
api_router.include_router(document_processing.router)

# Phase 3+: To be implemented
# api_router.include_router(rules.router)
# api_router.include_router(reports.router)