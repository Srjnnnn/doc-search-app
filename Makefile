.PHONY: help setup validate start stop clean logs build test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup of the project
	@echo "Setting up the project..."
	@mkdir -p data/documents logs scripts services/vector-db
	@cp .env.example .env 2>/dev/null || echo ".env already exists"
	@echo "✅ Project setup completed!"
	@echo "📝 Please edit .env file with your API keys"

validate: ## Validate environment configuration
	@echo "Validating environment..."
	@python scripts/validate-env.py

start: validate ## Start all services
	@echo "Starting all services..."
	@docker-compose up --build

start-detached: validate ## Start all services in background
	@echo "Starting all services in background..."
	@docker-compose up --build -d

stop: ## Stop all services
	@echo "Stopping all services..."
	@docker-compose down

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

logs: ## Show logs from all services
	@docker-compose logs -f

build: ## Build all services
	@docker-compose build

test: ## Run basic health checks
	@echo "Running health checks..."
	@curl -f http://localhost:8000/health || echo "API Gateway not responding"

restart: stop start ## Restart all services
