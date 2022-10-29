# makefile for Gymbuddies Python virtual environment

PYTHON = python3.10  # version >= 3.10 required for this project

install:
	$(PYTHON) -m venv venv              # makefile: Initialize a new python virtual environment
	bash vsetup.sh                      # makefile: Modify virtual environment activate script to set PYTHONPATH and DATABASE_URL
																			# makefile: Enter python virtual environment:
																			# makefile: Install requirements
																			# makefile: Install self as editable package (makes self accessible via imports, e.g. 'from gymbuddies.database import db')
	. venv/bin/activate; \
	python -m pip install --upgrade pip; \
	python -m pip install -r requirements.txt; \
	python -m pip install -e .
	# 
	# makefile: Setup complete. Use '. venv/bin/activate' to enter the project virtual environment.
	# makefile: Remember to set DATABASE_URL to the correct database URL, replacing 'postgres://' with 'postgresql://'.
