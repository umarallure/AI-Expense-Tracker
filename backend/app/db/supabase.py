"""
Supabase client configuration and database utilities.
Provides connection to Supabase PostgreSQL and Storage.
"""
from supabase import create_client, Client
from functools import lru_cache
from typing import Optional
from app.core.config import settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client instance (cached).
    Uses anon/public key for regular operations.

    Returns:
        Configured Supabase client
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


@lru_cache()
def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client instance (cached).
    Uses service role key for admin operations (bypasses RLS).

    Returns:
        Configured Supabase admin client
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


class SupabaseManager:
    """
    Helper class for common Supabase operations.
    """

    def __init__(self, client: Optional[Client] = None):
        """
        Initialize Supabase manager.

        Args:
            client: Optional Supabase client, creates new one if not provided
        """
        self.client = client or get_supabase_client()
    
    async def upload_file(
        self,
        bucket_name: str,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload a file to Supabase Storage.

        Args:
            bucket_name: Storage bucket name
            file_path: Path within bucket where file will be stored
            file_data: File content as bytes
            content_type: MIME type of the file

        Returns:
            Upload response with file information
        """
        options = {"content-type": content_type} if content_type else {}
        response = self.client.storage.from_(bucket_name).upload(
            file_path,
            file_data,
            options
        )
        return response
    
    async def get_file_url(
        self,
        bucket_name: str,
        file_path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Get a signed URL for a file in Supabase Storage.
        
        Args:
            bucket_name: Storage bucket name
            file_path: Path to file within bucket
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Signed URL for file access
        """
        response = self.client.storage.from_(bucket_name).create_signed_url(
            file_path,
            expires_in
        )
        return response.get("signedURL", "")
    
    async def delete_file(self, bucket_name: str, file_path: str) -> dict:
        """
        Delete a file from Supabase Storage.
        
        Args:
            bucket_name: Storage bucket name
            file_path: Path to file within bucket
            
        Returns:
            Delete response
        """
        response = self.client.storage.from_(bucket_name).remove([file_path])
        return response
    
    def execute_rpc(self, function_name: str, params: dict) -> dict:
        """
        Execute a PostgreSQL function via RPC.
        
        Args:
            function_name: Name of the PostgreSQL function
            params: Parameters to pass to the function
            
        Returns:
            Function execution result
        """
        response = self.client.rpc(function_name, params).execute()
        return response.data


# Global instances
supabase_client = get_supabase_client()
supabase_admin_client = get_supabase_admin_client()
supabase_manager = SupabaseManager(supabase_client)