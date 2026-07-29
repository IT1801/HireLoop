.PHONY: setup install run-backend run-frontend run

setup:
	uv venv
	uv add -r requirements.txt

install:
	uv add -r requirements.txt

run-backend:
	python -m uvicorn src.components.main:app --reload

run-frontend:
	PYTHONPATH=. python src/frontend/app.py

run:
	@echo "Starting HireLoop servers (Backend + Frontend)..."
	@$(MAKE) -j 2 run-backend run-frontend
