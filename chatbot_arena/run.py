#!/usr/bin/env python3
"""
Run script for the LLM Chatbot Arena Flask application.
"""

import sys
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to the path to ensure we can import the app
sys.path.insert(0, current_dir)

from app import app

if __name__ == '__main__':
    print("Starting LLM Chatbot Arena...")
    print("Open your browser and navigate to http://127.0.0.1:5000/")
    print("Looking for response files in notes/data directory...")
    app.run(debug=True, host='0.0.0.0', port=5000) 