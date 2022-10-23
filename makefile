# makefile for Gymbuddies Python virtual environment

init:
	python -m venv venv              # Initialize a new python virtual environment
	bash vsetup.sh                   # Modify virtual environment activate script to set PYTHONPATH and DATABASE_URL
	. venv/bin/activate              # Activate python virtual environment
	python -m pip install -r requirements.txt  # Install requirements
	python -m pip install -e .                 # Install self as editable package (makes self accessible via imports, e.g. 'from gymbuddies.database import db')
