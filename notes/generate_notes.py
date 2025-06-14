import os
from pathlib import Path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../medical_scribe"))
from app.services.note_generation_service import NoteGenerationService

# Models to use for generation
MODELS = [
    "deepseek-r1:7b",
    "deepseek-r1:32b",
    "llama3.2:3b",
    "llama3.1:8b",
    "gemma3:4b",
    "gemma3:27b",
    "qwen2.5:3b",
    "qwen3:32b",
    "mistral-small3.1:24b"
]

def process_transcription_file(file_path: Path, output_base_path: Path) -> None:
    """Process a single transcription file and generate clinical notes for all models."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            transcription = f.read()
        
        # Get the pathology and visit type from the directory structure
        pathology = file_path.parent.name
        visit_type = file_path.parent.parent.name
        
        # Create output directory structure
        output_path = output_base_path / visit_type / pathology
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate clinical notes for each model
        for model in MODELS:
            # Create model-specific output filename
            model_name = model.replace(":", "_")
            output_file = output_path / f"{file_path.stem}_{model_name}.txt"
            
            # Skip if the file already exists
            if output_file.exists():
                print(f"Skipping {output_file} - already exists")
                continue
                
            print(f"Generating clinical note for {file_path} using {model}")
            # Generate complete clinical note
            clinical_note = NoteGenerationService.generate_note_from_transcript(
                transcript=transcription,
                model=model
            )
            
            # Save final clinical note
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(clinical_note)
            print(f"Saved to: {output_file}")

                
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    interviews_path = Path("interviews/data")
    notes_path = Path("notes/data")
    
    # Create notes data directory if it doesn't exist
    notes_path.mkdir(parents=True, exist_ok=True)
    
    # Get all transcription files and sort them
    print(f"Looking for files in {interviews_path}")
    transcription_files = []
    for root, _, files in os.walk(interviews_path):
        for file in files:
            if file.endswith('.txt'):
                file_path = Path(root) / file
                transcription_files.append(file_path)
    
    # Sort files by path
    transcription_files.sort()
    
    # Process files in sorted order
    for file_path in transcription_files:
        print(f"Processing {file_path.name}")
        process_transcription_file(file_path, notes_path)

if __name__ == "__main__":
    main()
