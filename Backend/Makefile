# Use the Python executable to run commands
PYTHON = python3

# Default target to avoid issues with no target specified
.DEFAULT_GOAL := help

# Help text for targets
help:
	@echo "Available commands:"
	@echo "run         - Run the development server"
	@echo "mi    	   - Apply database migrations"
	@echo "make        - Create new migrations"
	@echo "shell       - Open the Django shell"
	@echo "test        - Run tests"
	@echo "superuser   - Create a superuser"
	@echo "clean       - Remove __pycache__ and *.pyc files"
	@echo "clean-migrations - Delete all migration files except __init__.py"
	@echo "static      - Collect static files"
	@echo ""
	@echo "Docker commands:"
	@echo "django-shell [env] - Open shell in Django container (env: local, test, prod)"
	@echo "django-logs [env]  - Show Django container logs (env: local, test, prod)"
	@echo "nginx-logs [env]   - Show Nginx container logs (env: local, test, prod)"
	@echo "redis-logs [env]   - Show Redis container logs (env: local, test, prod)"
	@echo "up [env]           - Start all Docker services (env: local, test, prod)"
	@echo "down [env]          - Stop all Docker services (env: local, test, prod)"
	@echo "build [env]         - Build and start Docker services (env: local, test, prod)"
	@echo "restart [env]       - Restart all Docker services (env: local, test, prod)"
	@echo ""
	@echo "Examples:"
	@echo "  make up           - Start local environment (default)"
	@echo "  make up test      - Start test environment"
	@echo "  make up prod      - Start production environment"
	@echo "  make django-shell test - Open shell in test Django container"

# Django commands
run:
	$(PYTHON) manage.py runserver

mi:
	$(PYTHON) manage.py migrate

make:
	$(PYTHON) manage.py makemigrations

shell:
	$(PYTHON) manage.py shell

test:
	$(PYTHON) manage.py test

superuser:
	$(PYTHON) manage.py createsuperuser

static:
	$(PYTHON) manage.py collectstatic

# Utility command
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Environment parameter (default to local)
ENV ?= local

# Docker commands
django-shell:
	docker exec -it $(shell docker ps -q -f name=$(ENV)_ProjectName_app) /bin/bash

django-logs:
	docker logs -f $(shell docker ps -q -f name=$(ENV)_ProjectName_app)

nginx-logs:
	docker logs -f $(shell docker ps -q -f name=$(ENV)_ProjectName_nginx)

redis-logs:
	docker logs -f $(shell docker ps -q -f name=$(ENV)_ProjectName_redis)

up:
	docker-compose -f Docker/docker-compose.$(ENV).yml up -d

down:
	docker-compose -f Docker/docker-compose.$(ENV).yml down

build:
	docker-compose -f Docker/docker-compose.$(ENV).yml up --build -d

restart:
	docker-compose -f Docker/docker-compose.$(ENV).yml restart
