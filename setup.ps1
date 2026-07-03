Write-Host "Setting up Python virtual environment..."
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements-dev.txt
Write-Host "Setup complete. Run '.venv\Scripts\Activate.ps1' to activate."
