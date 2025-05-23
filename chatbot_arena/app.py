import os
import random
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
import math
import pandas as pd

app = Flask(__name__)

# Define the supported models
MODELS = [
    "deepseek-r1_7b",
    "deepseek-r1_32b",
    "llama3.2_3b",
    "llama3.1_8b",
    "gemma3_4b",
    "gemma3_27b",
    "qwen2.5_3b",
    "qwen3_32b",
    "mistral-small3.1_24b"
]

# ELO rating constants
K = 32  # K-factor, determines how much ratings change after each match
DEFAULT_RATING = 1200  # Starting ELO rating for each model

# Store ratings and match history
RATINGS_FILE = os.path.join(os.path.dirname(__file__), 'ratings.json')
CONSULT_RATINGS_FILE = os.path.join(os.path.dirname(__file__), 'consult_ratings.json')
FOLLOWUP_RATINGS_FILE = os.path.join(os.path.dirname(__file__), 'followup_ratings.json')
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')

# Data directories
RESPONSES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notes', 'data')
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'interviews', 'data')

# Initialize or load ratings
# Separate ratings for general, consult, and follow-up
def load_ratings(rating_type='general'):
    ratings_map = {
        'general': RATINGS_FILE,
        'consult': CONSULT_RATINGS_FILE,
        'followup': FOLLOWUP_RATINGS_FILE
    }
    ratings_file = ratings_map[rating_type]
    if os.path.exists(ratings_file):
        with open(ratings_file, 'r') as f:
            return json.load(f)

    return {model: DEFAULT_RATING for model in MODELS}

# Initialize or load history
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

# Save ratings based on type
def save_ratings(ratings, rating_type='general'):
    ratings_map = {
        'general': RATINGS_FILE,
        'consult': CONSULT_RATINGS_FILE,
        'followup': FOLLOWUP_RATINGS_FILE
    }
    ratings_file = ratings_map[rating_type]
    with open(ratings_file, 'w') as f:
        json.dump(ratings, f, indent=2)

# Save history to file
def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

# Calculate expected score based on ELO rating
def expected_score(rating_a, rating_b):
    """
    Expected score for model A when playing against model B
    rating_a: rating of model A
    rating_b: rating of model B
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

# Update ELO ratings
def update_elo(rating_a, rating_b, result):
    """
    Update ELO ratings based on match result
    result: 1 if A wins, 0 if B wins, 0.5 for a draw
    """
    expected_a = expected_score(rating_a, rating_b)
    expected_b = expected_score(rating_b, rating_a)
    
    new_rating_a = rating_a + K * (result - expected_a)
    new_rating_b = rating_b + K * ((1 - result) - expected_b)
    
    return new_rating_a, new_rating_b

# Get all prompts from the prompts directory
def get_prompts():
    prompts = []
    
    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR)
        return []
    
    # Read prompts from interviews/data directory
    for root, dirs, files in os.walk(PROMPTS_DIR):
        for file in files:
            if file.endswith('.txt'):
                prompt_path = os.path.join(root, file)
                with open(prompt_path, 'r') as f:
                    prompt_text = f.read().strip()
                    prompt_id = os.path.splitext(file)[0]  # Use filename without extension as ID
                    prompts.append({'id': prompt_id, 'text': prompt_text})
    
    return prompts

# Find all response files for a given prompt
def find_response_files(prompt_id):
    response_files = {}
    
    # Walk through all subdirectories in notes/data
    for root, dirs, files in os.walk(RESPONSES_DIR):
        for file in files:
            if file.endswith('.txt') and file.startswith(f"{prompt_id}_"):
                # Extract model name from filename (part after first underscore, before .txt)
                model_name = file[len(prompt_id) + 1:].split('.txt')[0]
                if model_name in MODELS:
                    response_files[model_name] = os.path.join(root, file)
    
    return response_files

# Load Excel data for prompt types and lengths
def load_excel_data():
    excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_info', 'Fake OSCEs.xlsx')
    df = pd.read_excel(excel_path)
    return df[['file_name', 'type', 'length_s']]

@app.route('/')
def index():
    # Get ratings for displaying leaderboard
    general_ratings = load_ratings('general')
    consult_ratings = load_ratings('consult')
    followup_ratings = load_ratings('followup')
    sorted_general = sorted(general_ratings.items(), key=lambda x: x[1], reverse=True)
    sorted_consult = sorted(consult_ratings.items(), key=lambda x: x[1], reverse=True)
    sorted_followup = sorted(followup_ratings.items(), key=lambda x: x[1], reverse=True)
    
    # Get match history
    history = load_history()
    
    return render_template('index.html', 
                           general_leaderboard=sorted_general,
                           consult_leaderboard=sorted_consult,
                           followup_leaderboard=sorted_followup,
                           history=history[-10:])

@app.route('/arena')
def arena():
    prompts = get_prompts()
    
    if not prompts:
        return render_template('error.html', message="No prompts found. Please add prompt files to the 'interviews/data' directory.")
    
    # Randomly select a prompt
    selected_prompt = random.choice(prompts)
    prompt_id = selected_prompt['id']
    prompt_text = selected_prompt['text']
    
    # Get all model responses for this prompt
    response_files = find_response_files(prompt_id)
    available_models = list(response_files.keys())
    
    if len(available_models) < 2:
        return render_template('error.html', message=f"Not enough model responses for prompt '{prompt_id}'")
    
    # Randomly select two different models
    model_a, model_b = random.sample(available_models, 2)
    
    # Read response content
    with open(response_files[model_a], 'r') as f:
        response_a = f.read()
    
    with open(response_files[model_b], 'r') as f:
        response_b = f.read()
    
    return render_template('arena.html', 
                           prompt=prompt_text,
                           prompt_id=prompt_id,
                           response_a=response_a,
                           response_b=response_b,
                           model_a=model_a,
                           model_b=model_b)

@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    winner = data.get('winner')
    loser = data.get('loser')
    prompt_id = data.get('prompt_id')
    
    # Load Excel data
    excel_data = load_excel_data()
    prompt_type = excel_data[excel_data['file_name'] == prompt_id]['type'].values[0]
    length_s = int(excel_data[excel_data['file_name'] == prompt_id]['length_s'].values[0])
    
    # Load current ratings based on type
    old_ratings = load_ratings(prompt_type)
    new_ratings = old_ratings.copy()

    old_general_rating = load_ratings('general')
    new_general_rating = old_general_rating.copy()
    
    # Update ELO ratings
    new_ratings[winner], new_ratings[loser] = update_elo(old_ratings[winner], old_ratings[loser], 1)
    new_general_rating[winner], new_general_rating[loser] = update_elo(old_general_rating[winner], old_general_rating[loser], 1)

    # Save updated ratings
    save_ratings(new_ratings, prompt_type)
    save_ratings(new_general_rating, 'general')
    
    # Record match in history
    history = load_history()
    history.append({
        'timestamp': data.get('timestamp'),
        'prompt_id': prompt_id,
        'winner': winner,
        'loser': loser,
        'winner_old_rating': int(old_ratings[winner]),
        'loser_old_rating': int(old_ratings[loser]),
        'winner_new_rating': int(new_ratings[winner]),
        'loser_new_rating': int(new_ratings[loser]),
        'length_s': length_s,
        'type': prompt_type
    })
    save_history(history)
    
    return jsonify({
        'success': True,
        'new_winner_rating': new_general_rating[winner],
        'new_loser_rating': new_general_rating[loser]
    })

@app.route('/undo', methods=['POST'])
def undo():
    # Load history and ratings
    history = load_history()
    general_ratings = load_ratings('general')
    consult_ratings = load_ratings('consult')
    followup_ratings = load_ratings('followup')
    
    if not history:
        return jsonify({'success': False, 'message': 'No history to undo'})
    
    # Remove the last match
    last_match = history.pop()
    save_history(history)
    
    # Reset ratings to default if this is the only entry
    if not history:
        general_ratings = {model: DEFAULT_RATING for model in MODELS}
        consult_ratings = {model: DEFAULT_RATING for model in MODELS}
        followup_ratings = {model: DEFAULT_RATING for model in MODELS}
    else:
        # Recalculate all ratings from scratch
        general_ratings = {model: DEFAULT_RATING for model in MODELS}
        consult_ratings = {model: DEFAULT_RATING for model in MODELS}
        followup_ratings = {model: DEFAULT_RATING for model in MODELS}
        for match in history:
            winner = match['winner']
            loser = match['loser']
            match_type = match['type']
            general_ratings[winner], general_ratings[loser] = update_elo(general_ratings[winner], general_ratings[loser], 1)
            if match_type == 'consult':
                consult_ratings[winner], consult_ratings[loser] = update_elo(consult_ratings[winner], consult_ratings[loser], 1)
            elif match_type == 'followup':
                followup_ratings[winner], followup_ratings[loser] = update_elo(followup_ratings[winner], followup_ratings[loser], 1)
    
    save_ratings(general_ratings, 'general')
    save_ratings(consult_ratings, 'consult')
    save_ratings(followup_ratings, 'followup')
    
    return jsonify({
        'success': True,
        'undone_match': last_match
    })

@app.route('/stats')
def stats():
    general_ratings = load_ratings('general')
    consult_ratings = load_ratings('consult')
    followup_ratings = load_ratings('followup')
    history = load_history()
    
    # Calculate win rates for each model
    win_counts = {model: {'general': 0, 'consult': 0, 'followup': 0} for model in MODELS}
    match_counts = {model: {'general': 0, 'consult': 0, 'followup': 0} for model in MODELS}
    
    for match in history:
        winner = match['winner']
        loser = match['loser']
        match_type = match['type']
        win_counts[winner][match_type] += 1
        match_counts[winner][match_type] += 1
        match_counts[loser][match_type] += 1
        # General = consult + followup
        win_counts[winner]['general'] += 1
        match_counts[winner]['general'] += 1
        match_counts[loser]['general'] += 1
    
    win_rates = {model: {
        'general': (win_counts[model]['general'] / match_counts[model]['general']) * 100 if match_counts[model]['general'] > 0 else 0,
        'consult': (win_counts[model]['consult'] / match_counts[model]['consult']) * 100 if match_counts[model]['consult'] > 0 else 0,
        'followup': (win_counts[model]['followup'] / match_counts[model]['followup']) * 100 if match_counts[model]['followup'] > 0 else 0
    } for model in MODELS}
    
    # Sort models by ELO rating
    sorted_general = sorted(MODELS, key=lambda model: general_ratings[model], reverse=True)
    sorted_consult = sorted(MODELS, key=lambda model: consult_ratings[model], reverse=True)
    sorted_followup = sorted(MODELS, key=lambda model: followup_ratings[model], reverse=True)
    
    return render_template('stats.html', 
                           general_ratings=general_ratings, 
                           consult_ratings=consult_ratings, 
                           followup_ratings=followup_ratings, 
                           win_rates=win_rates,
                           match_counts=match_counts,
                           sorted_general=sorted_general,
                           sorted_consult=sorted_consult,
                           sorted_followup=sorted_followup,
                           total_matches=len(history))

if __name__ == '__main__':
    app.run(debug=True)