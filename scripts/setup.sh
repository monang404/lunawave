#!/bin/bash
echo "Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e .
pip install -r requirements-dev.txt
echo "Setup complete. Run 'source .venv/bin/activate' to activate."
