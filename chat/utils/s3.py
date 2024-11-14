# utils/s3.py
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging
import uuid
from django.core.files.base import ContentFile

def upload_to_s3(file_obj, folder="media"):
    """
    Upload a file to AWS S3 bucket
    
    Args:
        file_obj: Django UploadedFile object
        folder: The folder path within the bucket (default: 'media')
        
    Returns:
        tuple: (bool, str) -- (success status, url or error message)
    """
    # Get the file content before it's closed
    file_content = file_obj.read()
    file_obj.seek(0)  # Reset file pointer for any subsequent operations
    
    # Generate a unique filename
    file_extension = file_obj.name.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Generate the S3 path
    s3_path = f"{folder}/{unique_filename}"
    
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Create a new file-like object from the content
        content_file = ContentFile(file_content)
        
        # Upload file to S3
        s3_client.upload_fileobj(
            content_file,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_path,
            ExtraArgs={
                'ContentType': file_obj.content_type,
                'ACL': 'public-read'
            }
        )
        
        # Generate the URL for the uploaded file
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_path}"
        
        return True, s3_url
        
    except ClientError as e:
        logging.error(f"AWS S3 upload error: {e}")
        return False, str(e)
        
    except Exception as e:
        logging.error(f"Unexpected error during S3 upload: {e}")
        return False, "An unexpected error occurred during file upload"