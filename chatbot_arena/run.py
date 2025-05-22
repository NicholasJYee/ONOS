#!/usr/bin/env python3
"""
Run script for the LLM Chatbot Arena Flask application.
"""

import sys
import os\

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to the path to ensure we can import the app
sys.path.insert(0, current_dir)

from app import app

if __name__ == '__main__':
    port = 5000

    # Run Flask app on all interfaces
    app.run(debug=True, host='127.0.0.1', port=port) 