.DEFAULT_GOAL := help

UV ?= uv
DOCKER ?= docker
IMAGE ?= pyp2p-forca

.PHONY: help install setup hooks check lint format format-check fix typecheck test run docker-build docker-check

help:
	@printf '%s\n' \
	  'make setup         Instala dependências e hook de commit' \
	  'make install       Sincroniza a .venv usando uv.lock' \
	  'make hooks         Instala o hook neste clone' \
	  'make check         Executa lint, estilo, tipos e testes' \
	  'make lint          Verifica lint sem alterar arquivos' \
	  'make format        Formata o código' \
	  'make format-check  Verifica a formatação' \
	  'make fix           Corrige lint automaticamente e formata' \
	  'make typecheck     Verifica tipos com mypy estrito' \
	  'make test          Executa testes locais sem rede externa' \
	  'make run           Executa o exemplo Rendezvous (usa rede real)' \
	  'make docker-build  Constrói a imagem Linux e verifica o código' \
	  'make docker-check  Constrói a imagem e executa as verificações'

install:
	$(UV) sync --locked

setup: install
	$(UV) run --locked pre-commit install

hooks:
	$(UV) run --locked pre-commit install

check:
	$(UV) run --locked python scripts/check.py

lint:
	$(UV) run --locked ruff check .

format:
	$(UV) run --locked ruff format .

format-check:
	$(UV) run --locked ruff format --check .

fix:
	$(UV) run --locked ruff check --fix .
	$(UV) run --locked ruff format .

typecheck:
	$(UV) run --locked mypy

test:
	$(UV) run --locked python -m unittest discover -s tests

# src/main.py ainda está vazio; este alvo usa o exemplo existente.
run:
	$(UV) run --locked python -m src.network.rendezvous.teste

docker-build:
	$(DOCKER) build -t $(IMAGE) .

docker-check: docker-build
	$(DOCKER) run --rm $(IMAGE) uv run --locked python scripts/check.py
