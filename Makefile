build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f api

seed:
	python scripts/seed_knowledge.py

setup-db:
	python scripts/setup_supabase.py

status:
	docker-compose ps

first-run: build up
	@echo "Esperando a que los servicios arranquen..."
	sleep 10
	make seed
