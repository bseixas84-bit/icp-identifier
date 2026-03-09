.PHONY: install run api clean setup

# Setup everything from scratch
setup: venv install
	@echo "Setup complete. Run 'make run' to start."

# Create virtual environment
venv:
	python3.12 -m venv .venv

# Install dependencies
install:
	.venv/bin/pip install -r requirements.txt

# Run Streamlit app
run:
	.venv/bin/streamlit run app.py --server.port 8501

# Run FastAPI backend
api:
	.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Clean generated files
clean:
	rm -rf __pycache__ engine/__pycache__ dist build *.egg-info
	rm -f data/reports/*.md

# Package as distributable
package:
	.venv/bin/pip install build
	.venv/bin/python -m build
