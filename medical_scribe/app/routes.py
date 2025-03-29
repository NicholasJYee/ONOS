from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from app.services.audio_service import AudioService
from app.services.transcription_service import TranscriptionService
from app.services.note_generation_service import NoteGenerationService
import os

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/process-audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Save audio file
        audio_path = AudioService.save_audio(audio_file)
        
        # Transcribe audio
        transcript = TranscriptionService.transcribe_audio(audio_path)
        
        # Generate note
        note = NoteGenerationService.generate_note(transcript)
        
        # Get the filename for download
        filename = os.path.basename(audio_path)
        
        return jsonify({
            'transcript': transcript,
            'note': note,
            'audioPath': filename
        })
    except Exception as e:
        # Ensure cleanup even if processing fails
        if 'audio_path' in locals():
            AudioService.cleanup_audio(audio_path)
        return jsonify({'error': str(e)}), 500

@main.route('/download-audio/<filename>')
def download_audio(filename):
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404 