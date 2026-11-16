# Makefile — короткие имена для длинных команд.
# Вместо `docker compose up --build` пишешь `make up`.
# Список всех команд: make help

# Команды ниже — не имена файлов, а просто действия.
.PHONY: help up up-d down logs build test lint format shell migrate migration check-links backup

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-10s %s\n", $$1, $$2}'

up: ## Собрать и запустить приложение (остановить: Ctrl+C)
	docker compose up --build

up-d: ## Запустить в фоне (остановить: make down)
	docker compose up --build -d

down: ## Остановить приложение
	docker compose down

logs: ## Показать логи запущенного приложения
	docker compose logs -f app

build: ## Пересобрать образ без запуска
	docker compose build

test: ## Запустить тесты
	docker compose run --rm app pytest

lint: ## Проверить код линтером и форматтером
	docker compose run --rm app sh -c "ruff check . && ruff format --check ."

format: ## Автоматически исправить стиль кода
	docker compose run --rm -v "$(CURDIR)":/app app sh -c "ruff check --fix . && ruff format ."

shell: ## Открыть терминал внутри контейнера
	docker compose run --rm app bash

migrate: ## Применить миграции базы данных
	docker compose run --rm app alembic upgrade head

migration: ## Создать миграцию: make migration name=add_topics
	docker compose run --rm -v "$(CURDIR)":/app app alembic revision --autogenerate -m "$(name)"

check-links: ## Проверить, что ссылки в учебных материалах открываются (нужен интернет)
	docker compose run --rm app python -m app.tools.check_links

backup: ## Сохранить копию базы с прогрессом в data/backups/
	docker compose run --rm app python -m app.tools.backup
