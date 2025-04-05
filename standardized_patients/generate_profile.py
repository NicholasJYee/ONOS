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

FOLLOWUP_PERIODS = [
    ("early", 0.75, lambda: f"{random.randint(2, 12)} weeks"),
    ("middle", 0.20, lambda: f"{random.randint(3, 6)} months"),
    ("late", 0.05, lambda: f"{random.randint(1, 2)} years")
]

def setup_directories():
    """Create the necessary directory structure."""
    base_dir = "standardized_patients/data"
    visit_types = ["consults", "followups"]
    
    for visit in visit_types:
        for pathology in PATHOLOGIES:
            path = os.path.join(base_dir, visit, pathology.lower().replace(" ", "_"))
            os.makedirs(path, exist_ok=True)

def generate_prompt(pathology: str, is_followup: bool, followup_period: str = None) -> str:
    """Generate a prompt for the language model to create a patient profile."""
    
    if is_followup:
        base_prompt = f"""Generate a detailed followup patient profile for a patient with {pathology} 
        who is being seen {followup_period} after their initial injury. 

        The profile should include:
        1. Updated History:
           - Changes in symptoms since last visit
           - New medical history or complications
           - Changes in medications
           - Changes in social history
        
        2. Updated Physical Exam Findings:
           - Current range of motion
           - Strength testing
           - Special tests
           - Any new findings
        
        3. Updated Imaging Findings:
           - Comparison with previous imaging
           - New findings
           - Healing progress
        
        4. Assessment and Plan:
           - Current status
           - Progress since last visit
           - Next steps in treatment
           - Any modifications to treatment plan
        
        5. Patient Questions:
           - 3-5 realistic follow-up questions the patient might ask
           - Questions should be specific to their condition and recovery
        
        Format the response in clear sections with appropriate medical terminology.
        Make the case realistic with varying degrees of recovery and complications."""
    else:
        base_prompt = f"""Generate a detailed initial patient profile for a patient with {pathology}. 

        The profile should include:
        1. History:
           - Present illness and mechanism of injury
           - Past medical history
           - Past surgical history
           - Current medications
           - Allergies
           - Social history (occupation, smoking, alcohol, etc.)
        
        2. Physical Exam Findings:
           - General appearance
           - Vital signs
           - Specific exam findings related to injury
           - Range of motion
           - Strength testing
           - Special tests
           - Neurovascular status
        
        3. Imaging Findings:
           - X-ray findings
           - CT/MRI findings if applicable
           - Classification of injury if applicable
        
        4. Assessment and Plan:
           - Diagnosis
           - Treatment options
           - Recommended treatment plan
           - Expected recovery timeline
           - Follow-up schedule
        
        5. Patient Questions:
           - 3-5 realistic questions the patient might ask
           - Questions should be specific to their condition and treatment
        
        Format the response in clear sections with appropriate medical terminology.
        Make the case realistic with varying degrees of severity and complexity."""

    return base_prompt

def get_followup_period() -> str:
    """Determine the followup period based on weighted probabilities."""
    rand = random.random()
    cumulative = 0
    for period, prob, label in FOLLOWUP_PERIODS:
        cumulative += prob
        if rand <= cumulative:
            return label()
    return FOLLOWUP_PERIODS[-1][2]()

def generate_profile(prompt: str) -> str:
    """Generate a patient profile using Ollama."""
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
        raise Exception(f"Error generating profile: {e}")

def save_profile(content: str, filepath: str):
    """Save the generated profile to a file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_profiles(n_consults: int, m_followups: int):
    """Generate n consults and m followups for each pathology."""
    setup_directories()
    
    # Generate consults
    for i in range(n_consults):
        print(f"\nGenerating consult {i+1} of {n_consults} for all pathologies...")
        
        # Generate one consult for each pathology
        for pathology in PATHOLOGIES:
            print(f"Generating consult for {pathology}...")
            prompt = generate_prompt(pathology, False)
            profile = generate_profile(prompt)
            
            filename = f"{time.strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join("standardized_patients/data", "consults", 
                                    pathology.lower().replace(" ", "_"), 
                                    filename)
            save_profile(profile, filepath)
                
            # Generate followups for this consult
            for j in range(m_followups):
                followup_period = get_followup_period()
                prompt = generate_prompt(pathology, True, followup_period)
                followup = generate_profile(prompt)
                
                followup_filename = f"{time.strftime('%Y%m%d_%H%M%S')}.txt"
                followup_filepath = os.path.join("standardized_patients/data", "followups",
                                                pathology.lower().replace(" ", "_"),
                                                followup_filename)
                save_profile(followup, followup_filepath)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate standardized patient profiles')
    parser.add_argument('--n_consults', type=int, default=5,
                        help='Number of consults per pathology')
    parser.add_argument('--m_followups', type=int, default=1,
                        help='Number of followups per consult')
    
    args = parser.parse_args()
    
    generate_profiles(args.n_consults, args.m_followups)
