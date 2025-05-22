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
    # Run Flask app on all interfaces
    print(f"\nRun it on other devices on your network with: http://192.168.1.39:5000/")
    print(f"Run this to forward wsl-2 to windows (make sure port 5000 is open):")
    print(f"netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=5000 connectaddress=172.29.27.105 connectport=5000")
    print(f"Source: https://ersantana.com/devops/exposing-flask-app-on-wsl-to-local-network\n\n")
    app.run(host='0.0.0.0', port=5000) 
