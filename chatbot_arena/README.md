# LLM Chatbot Arena

A lightweight Flask application for comparing outputs from different open-source language models (LLMs) in a head-to-head competition format.

Nicholas J. Yee, MD

## Overview

This app implements a "chatbot arena" that allows users to compare responses from different LLMs to the same prompts. The app:

1. Randomly selects a prompt and two model responses
2. Presents them side-by-side for comparison
3. Allows users to vote for their preferred response
4. Tracks ELO ratings to rank the models based on user preferences

## Supported Models

The following models are currently supported:
- deepseek-r1:7b
- deepseek-r1:32b
- llama3.2:3b
- llama3.1:8b
- gemma3:4b
- gemma3:27b
- qwen2.5:3b
- qwen3:32b
- mistral-small3.1:24b

## Setup

1. Clone this repository
2. Ensure your model response files are in the `notes/data` directory (which is in the parent directory of the chatbot_arena folder) using the format: `{prompt}_{model}.txt`
   - For example: `question1_llama3.1:8b.txt`, `question1_gemma3:4b.txt`, etc.
3. Run the application: `python run.py` (you will need to update your requirements)
4. Open your browser and navigate to `http://127.0.0.1:5000/`

## File Naming Convention

The response files must follow this naming convention:
- `{prompt}_{model}.txt`

Where:
- `{prompt}` is an identifier for the prompt (e.g., "question1", "creative_task", etc.)
- `{model}` is one of the supported model names listed above

The app will search for response files in all subdirectories of the `notes/data` directory.

## Features

- Random selection of prompts and models for comparison
- Side-by-side display of model responses
- Visual elevation effect on hover
- ELO rating system to rank models
- Comprehensive statistics page
- Ability to undo the last vote
- Responsive design for mobile and desktop
