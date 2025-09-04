import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

class AudioService:
    @staticmethod
    def save_audio(audio_file, is_blob=False):
        extension = '.wav' if is_blob else os.path.splitext(audio_file.filename)[1]
        filename = f"{uuid.uuid4()}{extension}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        audio_file.save(filepath)
        return filepath
    
    @staticmethod
    def cleanup_audio(filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error cleaning up audio file: {str(e)}") 