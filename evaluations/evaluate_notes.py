import os
import re
import pandas as pd
from pathlib import Path
import json
from typing import Dict, List, Tuple
from ollama import Client

SYSTEM_PROMPT = """Please act as an impartial judge and evaluate the quality of a clinical Subjective, Objective, Assessment, Plan (SOAP) note provided by an AI assistant. Your evaluation must objectively assess the note using these four metrics: **clinical accuracy**, **completeness**, **conciseness**, and **clarity**.

Use the following criteria to assign numeric ratings (0–5) to each metric:

### Clinical Accuracy:
- **5:** Perfect clinical accuracy; no inaccuracies.
- **4:** Minor inaccuracies of no clinical consequence.
- **3:** Moderate inaccuracies, minor impact on clinical interpretation.
- **2:** Noticeable inaccuracies, potentially misleading clinically.
- **1:** Significant inaccuracies, substantially compromising clinical validity.
- **0:** Severe inaccuracies, completely misrepresenting clinical information.

### Completeness:
- **5:** Includes all clinically relevant information.
- **4:** Nearly complete, minor omissions of limited clinical importance.
- **3:** Moderately complete, some omissions of moderate clinical importance.
- **2:** Limited completeness, important clinical information omitted.
- **1:** Minimally complete, critical clinical information omitted.
- **0:** Essential clinical information entirely absent.

### Conciseness:
- **5:** Precisely summarized, essential points conveyed without redundancy.
- **4:** Mostly concise, minimal unnecessary information included.
- **3:** Moderately concise, some redundant or irrelevant details.
- **2:** Limited conciseness, significant redundancy or extraneous information.
- **1:** Poorly concise, predominantly redundant or irrelevant.
- **0:** Not concise, largely irrelevant, or severely redundant.

### Clarity:
- **5:** Highly clear, easily readable, logically organized.
- **4:** Mostly clear, minor readability or organizational issues.
- **3:** Moderately clear, occasional confusion due to language or organization.
- **2:** Limited clarity, substantial confusion from readability or organization.
- **1:** Poorly clear, difficult to interpret, significantly unclear.
- **0:** Completely unclear, unreadable, severely disorganized.

### **Hallucination Detection:**
Clearly state if the note contains hallucinated information—clinical details or statements that are not clinically appropriate or accurate, potentially misleading the clinical interpretation or patient management.

Clearly state numeric ratings and indicate hallucinations (if any) using this format (do not add any other text):

Clinical Accuracy: [X]
Completeness: [X]
Conciseness: [X]
Clarity: [X]
Hallucination: [Yes/No]

As an example, a good response will look like this:

Clinical Accuracy: [5]
Completeness: [4]
Conciseness: [3]
Clarity: [2]
Hallucination: [Yes]"""

def extract_ratings(response: str) -> Dict[str, float]:
    """Extract ratings from the LLM response."""
    ratings = {}
    
    # Extract numeric ratings
    for metric in ['Clinical Accuracy', 'Completeness', 'Conciseness', 'Clarity']:
        pattern = f"{metric}: \[(\d+)\]"
        match = re.search(pattern, response)
        if match:
            ratings[metric.lower().replace(' ', '_')] = float(match.group(1))
    
    # Extract hallucination
    hallucination_pattern = r"Hallucination: \[+(Yes|No)\]+"
    hallucination_match = re.search(hallucination_pattern, response)
    if hallucination_match:
        ratings['hallucination'] = hallucination_match.group(1)
    
    return ratings

def evaluate_note(note: str) -> Tuple[Dict[str, float], str]:
    """Evaluate a note using Mistral via Ollama."""
    prompt = f"""SOAP Note:
{note}

Please evaluate the SOAP note according to the criteria above."""

    try:
        client = Client()
        response = client.generate(
            model='mistral',
            prompt=prompt,
            system=SYSTEM_PROMPT
        )
        return extract_ratings(response['response']), response['response']
    except Exception as e:
        print(f"Error evaluating note: {e}")
        return None, str(e)

def find_note_files(base_dir: str) -> List[str]:
    """Find all note files."""
    note_files = []
    base_path = Path(base_dir)
    
    for note_file in base_path.rglob("*.txt"):
        note_files.append(str(note_file))
    
    return note_files

def main():
    # Find all note files
    note_files = find_note_files("notes/data")
    total_files = len(note_files)
    print(f"Found {total_files} note files to evaluate")
    
    results = []
    failed_evaluations = []
    
    for note_path in note_files:
        print(f"Evaluating {note_path}")
        
        # Read the file
        with open(note_path, 'r') as f:
            note = f.read()
        
        # Extract model info from filename
        model_info = Path(note_path).stem.split('_')
        model_name = model_info[2]
        model_size = model_info[3]
        
        # Evaluate the note
        ratings, raw_response = evaluate_note(note)
        if ratings:
            result = {
                'note_path': note_path,
                'model_used': model_name,
                'model_size': model_size,
                **ratings
            }
            results.append(result)
        else:
            failed_evaluations.append({
                'note_path': note_path,
                'model_used': model_name,
                'model_size': model_size,
                'error': raw_response
            })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    df.to_csv('evaluations/soap_note_evaluations.csv', index=False)
    
    # Save failed evaluations to a separate CSV
    if failed_evaluations:
        failed_df = pd.DataFrame(failed_evaluations)
        failed_df.to_csv('evaluations/failed_evaluations.csv', index=False)
    
    # Print summary
    successful = len(results)
    failed = len(failed_evaluations)
    print(f"\nEvaluation Summary:")
    print(f"Total files processed: {total_files}")
    print(f"Successfully evaluated: {successful}")
    print(f"Failed evaluations: {failed}")
    print(f"Success rate: {(successful/total_files)*100:.1f}%")
    
    if failed_evaluations:
        print("\nFailed Evaluations:")
        for fail in failed_evaluations:
            print(f"\nFile: {fail['note_path']}")
            print(f"Model: {fail['model_used']} ({fail['model_size']})")
            print(f"Error: {fail['error']}")

if __name__ == "__main__":
    main()
