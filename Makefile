.PHONY: dev backend frontend install clean

install:
	cd backend && uv sync
	cd frontend && npm install

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) backend & $(MAKE) frontend & wait

clean:
	find backend -type d -name __pycache__ -exec rm -rf {} +
	rm -f backend/techpark_hunter.db
