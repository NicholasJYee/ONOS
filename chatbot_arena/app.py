import os
import random
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
import math

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
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')

# Data directories
RESPONSES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notes', 'data')
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'interviews', 'data')

# Initialize or load ratings
def load_ratings():
    if os.path.exists(RATINGS_FILE):
        with open(RATINGS_FILE, 'r') as f:
            return json.load(f)
    return {model: DEFAULT_RATING for model in MODELS}

# Initialize or load history
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

# Save ratings to file
def save_ratings(ratings):
    with open(RATINGS_FILE, 'w') as f:
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

@app.route('/')
def index():
    # Get ratings for displaying leaderboard
    ratings = load_ratings()
    sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    
    # Get match history
    history = load_history()
    
    return render_template('index.html', ratings=sorted_ratings, history=history[-10:])

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
    
    # Load current ratings
    old_ratings = load_ratings()
    new_ratings = old_ratings.copy()
    
    # Update ELO ratings
    new_ratings[winner], new_ratings[loser] = update_elo(old_ratings[winner], old_ratings[loser], 1)
    
    # Save updated ratings
    save_ratings(new_ratings)
    
    # Record match in history
    history = load_history()
    history.append({
        'timestamp': data.get('timestamp'),
        'prompt_id': prompt_id,
        'winner': winner,
        'loser': loser,
        'winner_old_rating': old_ratings[winner],
        'loser_old_rating': old_ratings[loser],
        'winner_new_rating': new_ratings[winner],
        'loser_new_rating': new_ratings[loser]
    })
    save_history(history)
    
    return jsonify({
        'success': True,
        'new_winner_rating': new_ratings[winner],
        'new_loser_rating': new_ratings[loser]
    })

@app.route('/undo', methods=['POST'])
def undo():
    # Load history and ratings
    history = load_history()
    ratings = load_ratings()
    
    if not history:
        return jsonify({'success': False, 'message': 'No history to undo'})
    
    # Remove the last match
    last_match = history.pop()
    save_history(history)
    
    # Reset ratings to default if this is the only entry
    if not history:
        ratings = {model: DEFAULT_RATING for model in MODELS}
    else:
        # Recalculate all ratings from scratch
        ratings = {model: DEFAULT_RATING for model in MODELS}
        for match in history:
            winner = match['winner']
            loser = match['loser']
            ratings[winner], ratings[loser] = update_elo(ratings[winner], ratings[loser], 1)
    
    save_ratings(ratings)
    
    return jsonify({
        'success': True,
        'undone_match': last_match
    })

@app.route('/stats')
def stats():
    ratings = load_ratings()
    history = load_history()
    
    # Calculate win rates for each model
    win_counts = {model: 0 for model in MODELS}
    match_counts = {model: 0 for model in MODELS}
    
    for match in history:
        winner = match['winner']
        loser = match['loser']
        win_counts[winner] += 1
        match_counts[winner] += 1
        match_counts[loser] += 1
    
    win_rates = {model: (win_counts[model] / match_counts[model]) * 100 if match_counts[model] > 0 else 0 
                for model in MODELS}
    
    # Sort models by ELO rating
    sorted_models = sorted(MODELS, key=lambda model: ratings[model], reverse=True)
    
    return render_template('stats.html', 
                           ratings=ratings, 
                           win_rates=win_rates,
                           match_counts=match_counts,
                           sorted_models=sorted_models,
                           total_matches=len(history))

if __name__ == '__main__':
    app.run(debug=True)