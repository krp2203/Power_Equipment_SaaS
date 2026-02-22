import os
from google.cloud import storage
from flask import current_app, g

def upload_for_tenant(file_storage, folder='uploads'):
    """
    Uploads a file to GCS with mandatory tenant isolation.
    Path: gs://{bucket}/{organization_id}/{folder}/{filename}
    """
    if not g.get('current_org_id'):
        raise ValueError("Security Error: Attempting to upload file without Tenant Context.")
    
    bucket_name = current_app.config['GCS_BUCKET']
    if not bucket_name:
        # Fallback for local dev if no bucket - maybe save to disk?
        # For now, just logging warning or error. 
        # Ideally, we mock this in dev.
        return None

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Sanitize filename
    from werkzeug.utils import secure_filename
    filename = secure_filename(file_storage.filename)
    
    # Construct isolated path
    blob_path = f"{g.current_org_id}/{folder}/{filename}"
    blob = bucket.blob(blob_path)
    
    blob.upload_from_file(file_storage, content_type=file_storage.content_type)
    
    # Return signed URL or public URL depending on policy.
    # For private assets, we usually generate signed URLs on retrieval.
    # Here we return the storage path to save in DB.
    return blob_path
