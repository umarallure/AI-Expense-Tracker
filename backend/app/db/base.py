"""
SQLAlchemy base configuration and declarative base.
Provides the base class for all database models.
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()