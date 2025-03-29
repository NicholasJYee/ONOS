import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import sys
# Fix the import path to properly find the medical_scribe app
sys.path.append(os.path.join(os.path.dirname(__file__), "../medical_scribe"))
from app.services.note_generation_service import NoteGenerationService

# Models to use for generation
MODELS = [
    "llama3.2:1b",
    "gemma3:1b",
    "qwen2.5:1.5b",
    "qwen2.5:0.5b",
    "deepseek-r1:1.5b"
]

def process_transcription_file(file_path: Path, output_base_path: Path) -> None:
    """Process a single transcription file and generate SOAP notes for all models."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            transcription = f.read()
        
        # Create output directory structure
        interviews_base = file_path.parent
        relative_path = file_path.relative_to(interviews_base)
        output_path = output_base_path / relative_path.parent
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate SOAP notes for each model
        for model in MODELS:
            print(f"Generating SOAP note for {file_path} using {model}")
            try:
                soap_note = NoteGenerationService.generate_note(transcription, model)
                
                # Create output filename with model name
                model_name = model.replace(":", "_")
                output_file = output_path / f"{file_path.stem}_{model_name}.txt"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(soap_note)
                print(f"Generated SOAP note saved to {output_file}")
            except Exception as e:
                print(f"Failed to generate SOAP note for {file_path} using {model}: {e}")
                
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    # Base paths - use relative paths
    interviews_path = Path("interviews/data")
    notes_path = Path("notes/data")
    
    # Create notes data directory if it doesn't exist
    notes_path.mkdir(parents=True, exist_ok=True)
    
    # Process all transcription files
    print(f"Looking for files in {interviews_path}")
    for root, _, files in os.walk(interviews_path):
        for file in files:
            if file.endswith('.txt'):
                print(f"Processing {file}")
                file_path = Path(root) / file
                process_transcription_file(file_path, notes_path)

if __name__ == "__main__":
    main()
