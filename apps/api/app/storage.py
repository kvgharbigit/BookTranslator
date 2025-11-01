import boto3
from botocore.exceptions import ClientError
from typing import Optional

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class R2Storage:
    """Cloudflare R2 storage client with S3 API compatibility."""
    
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name=settings.r2_region,
        )
        self.bucket = settings.r2_bucket
    
    def generate_presigned_upload_url(
        self,
        key: str,
        content_type: str = "application/epub+zip",
        expires_in: int = 3600
    ) -> str:
        """Generate presigned PUT URL for file upload."""
        try:
            url = self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            logger.info(f"Generated presigned upload URL for key: {key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise
    
    def generate_presigned_download_url(
        self,
        key: str,
        expires_in: Optional[int] = None
    ) -> str:
        """Generate presigned GET URL for file download."""
        if expires_in is None:
            expires_in = settings.signed_get_ttl_seconds
        
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                },
                ExpiresIn=expires_in,
            )
            logger.info(f"Generated presigned download URL for key: {key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise
    
    def upload_file(self, local_path: str, key: str, content_type: str = "application/octet-stream") -> bool:
        """Upload file to R2."""
        try:
            self.client.upload_file(
                local_path,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type}
            )
            logger.info(f"Uploaded file to R2: {local_path} -> {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file to R2: {e}")
            return False
    
    def download_file(self, key: str, local_path: str) -> bool:
        """Download file from R2."""
        try:
            self.client.download_file(self.bucket, key, local_path)
            logger.info(f"Downloaded file from R2: {key} -> {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file from R2: {e}")
            return False
    
    def get_object_size(self, key: str) -> Optional[int]:
        """Get object size in bytes."""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=key)
            size = response["ContentLength"]
            logger.info(f"Got object size for {key}: {size} bytes")
            return size
        except ClientError as e:
            logger.error(f"Failed to get object size: {e}")
            return None
    
    def delete_object(self, key: str) -> bool:
        """Delete object from R2."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted object from R2: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object from R2: {e}")
            return False


# Global storage instance - lazy loaded
storage = None

def get_storage():
    """Get R2 storage instance."""
    global storage
    if storage is None:
        # Always use R2 storage (production-ready)
        storage = R2Storage()
        logger.info(f"Using R2 storage: {settings.r2_bucket}")
    return storage