# makefile for Gymbuddies Python virtual environment

PYTHON = python3

install:
	$(PYTHON) -m venv venv                 # Initialize a new python virtual environment
	bash vsetup.sh                      # Modify virtual environment activate script to set PYTHONPATH and DATABASE_URL
																			# Enter python virtual environment:
	. venv/bin/activate; \
	pip install -r requirements.txt; \
	pip install -e .
																			# Install requirements
																			# Install self as editable package (makes self accessible via imports, e.g. 'from gymbuddies.database import db')
	echo "Setup complete. Use '. venv/bin/activate' to enter the project virtual environment."
