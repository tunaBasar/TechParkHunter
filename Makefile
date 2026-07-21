.PHONY: dev backend frontend install clean scrape scrape-all

install:
	cd backend && uv sync
	cd backend && uv run playwright install chromium
	cd frontend && npm install
	@echo "✅ Kurulum tamamlandı!"

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) backend & $(MAKE) frontend & wait

scrape:
	@if [ -z "$(SITE)" ]; then echo "Kullanım: make scrape SITE=odtu_teknokent"; exit 1; fi
	curl -s -X POST http://localhost:8000/api/scrape/$(SITE) | python3 -m json.tool

scrape-all:
	@for site in $$(curl -s http://localhost:8000/api/scrape/sites | python3 -c "import sys,json;[print(s['slug']) for s in json.load(sys.stdin)]"); do \
		echo "⏳ Scraping $$site..."; \
		curl -s -X POST http://localhost:8000/api/scrape/$$site | python3 -m json.tool; \
		sleep 3; \
	done
	@echo "✅ Tüm siteler scrape edildi!"

clean:
	find backend -type d -name __pycache__ -exec rm -rf {} +
	rm -f backend/techpark_hunter.db
	rm -rf backend/data/companies/*.json
	@echo "🧹 Temizlendi!"
