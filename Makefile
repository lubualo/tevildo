.PHONY: help up down logs shell migration migrate db-reset db-inspect db-shell rebuild test clean

# Default target - show help
help:
	@echo "🐱 Tevildo - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make up          - Start all services (with build)"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - Show logs (follow mode)"
	@echo "  make shell       - Open shell in backend container"
	@echo "  make rebuild     - Force rebuild without cache"
	@echo ""
	@echo "Database:"
	@echo "  make migration   - Generate new Alembic migration (requires msg=\"...\")"
	@echo "  make migrate     - Apply pending migrations"
	@echo "  make db-inspect  - Show all database tables"
	@echo "  make db-shell    - Open SQLite shell for database"
	@echo "  make db-reset    - Reset database (destroy + recreate)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       - Remove containers, volumes, and build cache"
	@echo "  make test        - Run tests (when implemented)"

# Start services (migrations run automatically)
up:
	docker compose up --build

# Stop services
down:
	docker compose down

# Show logs
logs:
	docker compose logs -f backend

# Open shell in backend container (works on Windows/Mac/Linux)
shell:
	docker compose exec backend bash

# Generate new migration (with message)
# Usage: make migration msg="add user table"
migration:
ifndef msg
	$(error msg is required. Usage: make migration msg="your message")
endif
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# Apply pending migrations
migrate:
	docker compose exec backend alembic upgrade head

# Reset database - cross-platform version
db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@pause
	docker compose exec backend rm -f /app/data/app.db
	docker compose exec backend alembic upgrade head

# Clean up everything - ONLY this project's containers/images
clean:
	@echo "🧹 Cleaning up Tevildo containers and volumes..."
	docker compose down -v --remove-orphans
	@echo "🗑️  Removing Tevildo images..."
	docker compose down --rmi local
	@echo "✅ Done! (Only Tevildo resources removed)"

# Inspect database tables
db-inspect:
	docker compose exec backend sqlite3 /app/data/app.db ".tables"

# Open SQLite shell for database
db-shell:
	docker compose exec backend sqlite3 /app/data/app.db

# Force rebuild without cache
rebuild:
	docker compose build --no-cache
	docker compose up

# Run tests (placeholder for future)
test:
	docker compose exec backend pytest
