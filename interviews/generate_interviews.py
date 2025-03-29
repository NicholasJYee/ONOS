import os
import random
from typing import List, Dict
import ollama
import time

# Constants
PATHOLOGIES = [
    "Distal radius fractures", "ankle fractures", "hip fractures", 
    "proximal humerus fractures", "tibial shaft fractures", 
    "fifth metatarsal fracture", "Lisfranc injuries", "calcaneus fractures",
    "patellar fractures", "elbow fractures", "scaphoid fractures",
    "acetabular fractures", "pelvic ring fractures", "tibial plateau fractures",
    "femoral shaft fractures", "pilon fractures", "scapular fractures",
    "clavicle fractures", "shoulder dislocations", "quadricep tendon ruptures",
    "bicep tendon ruptures", "Achilles tendon ruptures", "septic arthritis"
]

COMPLICATIONS = [
    "infection", "non-union", "malunion", "hardware failure", 
    "hardware irritation", "persistent pain", "functional limitation",
    "paresthesia", "weakness", "stiffness", "delayed healing"
]

FOLLOWUP_PERIODS = [
    ("early", 0.75, "2-12 weeks"),
    ("middle", 0.20, "3-6 months"),
    ("late", 0.05, "1-2 years")
]

def setup_directories():
    """Create the necessary directory structure."""
    base_dir = "interviews/data"
    visit_types = ["consults", "followups"]
    
    for visit in visit_types:
        for pathology in PATHOLOGIES:
            path = os.path.join(base_dir, visit, pathology.lower().replace(" ", "_"))
            os.makedirs(path, exist_ok=True)

def generate_prompt(pathology: str, is_followup: bool, followup_period: str = None) -> str:
    """Generate a prompt for the language model."""
    
    if is_followup:
        base_prompt = f"""Generate a followup medical interview transcript for a patient with {pathology} 
        who is being seen {followup_period} after their initial injury. 

        The interview should be a natural conversation that includes:
        1. Brief confirmation of injury and time since injury
        2. How they've been doing since last visit
        3. Current symptoms and functional status
        4. Relevant physical exam findings
        5. Review of any new imaging (if applicable)
        6. Brief assessment and plan
        
        Format the response as a natural back-and-forth conversation without using "Doctor:" or "Patient:" 
        labels. Keep it concise and focused on changes since last visit. Include relevant medical terminology 
        while keeping patient responses in lay language. Don't add line breaks.

        Example format:
        Good morning. How have you been doing since we last saw you? Much better, doctor. The pain has improved a lot.
        
        [Continue in this conversational format...]"""
    else:
        base_prompt = f"""Generate a detailed medical interview transcript for a patient with {pathology}. 

        The interview should be a natural conversation that includes:
        1. Initial greeting and patient identification
        2. History of injury/condition and mechanism
        3. Symptoms and functional limitations
        4. Physical examination findings and observations
        5. Discussion of imaging results (if applicable)
        6. Treatment plan discussion
        7. Patient questions and concerns
        
        Format the response as a natural back-and-forth conversation without using "Doctor:" or "Patient:" 
        labels. The doctor should introduce themselves at the start. Include relevant medical terminology 
        while keeping patient responses in lay language. Make the case realistic with varying degrees 
        of severity and outcomes. Don't add line breaks.

        Example format:
        Good morning. What brings you in to clinic today? I was playing soccer when I was involved in a tackle. I feel awkwardly onto my right side.
        
        [Continue in this conversational format...]"""

    return base_prompt

def get_followup_period() -> str:
    """Determine the followup period based on weighted probabilities."""
    rand = random.random()
    cumulative = 0
    for period, prob, label in FOLLOWUP_PERIODS:
        cumulative += prob
        if rand <= cumulative:
            return label
    return FOLLOWUP_PERIODS[-1][2]

def generate_interview(prompt: str) -> str:
    """Generate an interview using Ollama."""
    try:
        response = ollama.generate(
            model='phi3:14b',
            prompt=prompt,
            options={
                'temperature': 0.7,
                'num_predict': 2000
            },
        )
        return response['response']
    except Exception as e:
        raise Exception (f"Error generating interview: {e}")

def save_interview(content: str, filepath: str):
    """Save the generated interview to a file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_interviews(n_consults: int, m_followups: int):
    """Generate n consults and m followups for each pathology."""
    setup_directories()
    
    for pathology in PATHOLOGIES:
        print(f"Generating interviews for {pathology}...")
        
        # Generate consults
        for i in range(n_consults):
            prompt = generate_prompt(pathology, False)
            interview = generate_interview(prompt)
            
            filename = f"{time.strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join("interviews/data", "consults", 
                                    pathology.lower().replace(" ", "_"), 
                                    filename)
            save_interview(interview, filepath)
                
            # Generate followups for this consult
            for j in range(m_followups):
                followup_period = get_followup_period()
                prompt = generate_prompt(pathology, True, followup_period)
                followup = generate_interview(prompt)
                
                followup_filename = f"{time.strftime('%Y%m%d_%H%M%S')}.txt"
                followup_filepath = os.path.join("interviews/data", "followups",
                                                pathology.lower().replace(" ", "_"),
                                                followup_filename)
                save_interview(followup, followup_filepath)
                        
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic patient interviews')
    parser.add_argument('--n_consults', type=int, default=2,
                        help='Number of consults per pathology')
    parser.add_argument('--m_followups', type=int, default=1,
                        help='Number of followups per consult')
    
    args = parser.parse_args()
    
    generate_interviews(args.n_consults, args.m_followups)
