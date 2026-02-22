import os
import uuid
import shutil
import tempfile
from flask import request, jsonify, current_app, g

# Temporary directory for storing chunks during upload
CHUNK_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'media_chunks')

def ensure_chunk_dir():
    """Ensure chunk temporary directory exists"""
    os.makedirs(CHUNK_TEMP_DIR, exist_ok=True)

def init_chunk_upload():
    """Initialize chunked upload session"""
    try:
        ensure_chunk_dir()
        upload_id = str(uuid.uuid4())

        # Create upload session directory
        session_dir = os.path.join(CHUNK_TEMP_DIR, upload_id)
        os.makedirs(session_dir, exist_ok=True)

        current_app.logger.info(f"Initialized chunked upload: {upload_id}")
        return jsonify({'uploadId': upload_id})
    except Exception as e:
        current_app.logger.error(f"Error initializing chunk upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

def upload_chunk():
    """Handle individual chunk upload"""
    try:
        upload_id = request.form.get('uploadId')
        chunk_index = request.form.get('chunkIndex', type=int)
        total_chunks = request.form.get('totalChunks', type=int)

        if not upload_id or chunk_index is None:
            return jsonify({'error': 'Missing uploadId or chunkIndex'}), 400

        if 'chunk' not in request.files:
            return jsonify({'error': 'No chunk data provided'}), 400

        chunk_file = request.files['chunk']
        if not chunk_file:
            return jsonify({'error': 'Empty chunk file'}), 400

        # Save chunk to session directory
        session_dir = os.path.join(CHUNK_TEMP_DIR, upload_id)
        os.makedirs(session_dir, exist_ok=True)

        chunk_path = os.path.join(session_dir, f'chunk_{chunk_index}')
        chunk_file.save(chunk_path)

        current_app.logger.info(f"Received chunk {chunk_index + 1}/{total_chunks} for upload {upload_id}")

        return jsonify({
            'success': True,
            'chunkIndex': chunk_index,
            'totalChunks': total_chunks
        })
    except Exception as e:
        current_app.logger.error(f"Error uploading chunk: {str(e)}")
        return jsonify({'error': str(e)}), 500

def assemble_chunks(upload_id, org_id):
    """Assemble chunks into final file and save to permanent location"""
    try:
        ensure_chunk_dir()

        # Session directory with chunks
        session_dir = os.path.join(CHUNK_TEMP_DIR, upload_id)
        if not os.path.exists(session_dir):
            raise ValueError(f"Upload session {upload_id} not found")

        # Get list of chunks and sort by index
        chunk_files = sorted(
            [f for f in os.listdir(session_dir) if f.startswith('chunk_')],
            key=lambda x: int(x.split('_')[1])
        )

        if not chunk_files:
            raise ValueError(f"No chunks found for upload {upload_id}")

        # Create permanent filename with UUID
        unique_filename = f"{uuid.uuid4().hex}.mp4"

        # Create permanent upload directory
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'media', str(org_id))
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_filename)

        # Assemble chunks into final file
        with open(file_path, 'wb') as final_file:
            for chunk_filename in chunk_files:
                chunk_path = os.path.join(session_dir, chunk_filename)
                with open(chunk_path, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())

        # Clean up temporary chunks
        try:
            shutil.rmtree(session_dir)
        except Exception as e:
            current_app.logger.warning(f"Failed to clean up temp chunks: {str(e)}")

        current_app.logger.info(f"Assembled {len(chunk_files)} chunks into {file_path}")
        return unique_filename, file_path

    except Exception as e:
        current_app.logger.error(f"Error assembling chunks: {str(e)}")
        raise
