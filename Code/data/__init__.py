"""
Phase 1 - Data Ingestion Module
Handles API fetching, database connections, and data loading
"""

from .db_connection import engine

__all__ = ['engine']
