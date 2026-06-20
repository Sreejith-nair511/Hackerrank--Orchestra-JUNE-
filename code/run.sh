#!/bin/bash
# run.sh
# Script to run the evaluation pipeline and package the code

# Install requirements (uncomment if needed)
# pip install -r requirements.txt

# Run the main pipeline (make sure Python is accessible as 'python')
echo "Running the MCIS pipeline..."
python main.py

# Package deliverables
echo "Packaging code.zip..."
# Exclude unnecessary files
zip -r ../code.zip . -x "*/__pycache__/*" "*/.venv/*" "*.zip"

echo "Done! Deliverables ready: code.zip, output.csv (in dataset folder or outputs), and log.txt (in logs)."
