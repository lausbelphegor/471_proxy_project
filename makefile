.PHONY: no-op install uninstall freeze update-requirements activate deactivate clean test help

no-op:
	@echo "No operation"

run:
	python main.py

create-venv:
	python -m venv .venv-3.10.5

install:
	pip install -r requirements.txt

uninstall: freeze
	pip uninstall -y -r freeze.txt

freeze:
	pip freeze > freeze.txt

update-requirements:
	pip freeze > requirements.txt

activate:
	@echo "Run './.venv-3.10.5/Scripts/Activate.ps1' in your shell to activate the virtual environment."

deactivate:
	@echo "Run 'deactivate' in your shell to deactivate the virtual environment."

clean:
	rm -rf __pycache__ *.pyc *.pyo *.pyd *.log

test:
	python -m unittest discover -s tests

help:
	@echo "Available targets:"
	@echo "  no-op          - No operation"
	@echo "  run            - Run the main.py script"
	@echo "  create-venv    - Create a virtual environment"
	@echo "  install        - Install the dependencies from requirements.txt"
	@echo "  uninstall      - Uninstall the dependencies listed in freeze.txt"
	@echo "  freeze         - Save the current dependencies to freeze.txt"
	@echo "  update-requirements - Update requirements.txt with current dependencies"
	@echo "  activate       - Activate the virtual environment"
	@echo "  deactivate     - Deactivate the virtual environment (manual step)"
	@echo "  clean          - Remove temporary files"
	@echo "  test           - Run tests"
	@echo "  help           - Show this help message"
