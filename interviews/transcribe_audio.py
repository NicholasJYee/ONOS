import os
from pathlib import Path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../medical_scribe"))
from app.services.transcription_service import TranscriptionService

def transcribe_mock_interviews():
    # Define paths
    input_dir = Path("interviews/mock_interviews")
    output_dir = Path("interviews/data/mock_interviews")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all audio files from input directory
    audio_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg', '.wma')):
                audio_files.append(Path(root) / file)
    
    if not audio_files:
        print(f"No audio files found in {input_dir}")
        return
    
    print(f"Found {len(audio_files)} audio files to transcribe")
    
    # Process each audio file
    for audio_file in audio_files:
        try:
            print(f"Processing {audio_file.name}...")
            
            # Transcribe the audio
            transcript = TranscriptionService.transcribe_audio(str(audio_file))
            
            # Create output filename (same name as input but with .txt extension)
            output_file = output_dir / f"{audio_file.stem}.txt"
            
            # Save the transcript
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            print(f"Successfully transcribed {audio_file.name} to {output_file}")
            
        except Exception as e:
            print(f"Error processing {audio_file.name}: {str(e)}")

if __name__ == "__main__":
    transcribe_mock_interviews()
