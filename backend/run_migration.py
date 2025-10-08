"""
Run database migration to add transaction links to documents table.
"""
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Read migration SQL
migration_file = Path(__file__).parent / "migrations" / "add_transaction_link_to_documents.sql"
with open(migration_file, "r") as f:
    migration_sql = f.read()

logger.info("Running migration: add_transaction_link_to_documents.sql")
logger.info(f"Migration SQL:\n{migration_sql}\n")

try:
    # Execute migration using RPC function or direct SQL execution
    # Note: Supabase Python client doesn't have direct SQL execution
    # You'll need to run this via Supabase Dashboard > SQL Editor or using psycopg2
    
    logger.warning(
        "\n" + "="*80 + "\n"
        "⚠️  MANUAL MIGRATION REQUIRED\n"
        "="*80 + "\n"
        "The Supabase Python client doesn't support direct SQL execution.\n"
        "Please run the migration manually:\n\n"
        "1. Go to your Supabase Dashboard\n"
        "2. Navigate to SQL Editor\n"
        "3. Copy and paste the migration SQL from:\n"
        f"   {migration_file}\n"
        "4. Click 'Run' to execute the migration\n"
        "="*80 + "\n"
    )
    
    # Alternative: If you have direct PostgreSQL access
    print("\n" + "="*80)
    print("MIGRATION SQL TO RUN:")
    print("="*80)
    print(migration_sql)
    print("="*80 + "\n")
    
except Exception as e:
    logger.error(f"Migration failed: {str(e)}")
    raise

logger.info("✅ Migration information displayed. Please run manually in Supabase Dashboard.")
