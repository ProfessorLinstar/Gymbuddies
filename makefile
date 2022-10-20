# makefile for Gymbuddies Python virtual environment
init:
	python -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt
	pip install -e .
