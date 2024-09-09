#!/bin/bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package and dependencies
pip install -e .

pip install -r requirements.txt

echo "Setup complete."
