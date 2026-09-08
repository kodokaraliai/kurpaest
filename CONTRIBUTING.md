# Contributing

This is a kodokaraliai group repo. The work split lives in [docs/architecture.md](docs/architecture.md) (sections **Work packages**) and in GitHub issues that 1:1 those packages.

## Setup

```bash
uv sync --group dev
cd frontend && npm install
```

## Python

- Package and versions: **uv** (`uv lock`, `uv sync`). Do not add a pip-only workflow.
- Format and lint: **ruff**.

```bash
uv run ruff format
uv run ruff check
uv run pytest
```

Domain query/filter code belongs in modules that do not import FastAPI. The HTTP app is a seam (see the architecture doc).

## Frontend

```bash
cd frontend
npm run dev      # served origin — required
npm run build
```

Do not instruct anyone to open the built files via `file://`.

## Issues

Claim the GitHub issue before you start (assign yourself): [kodokaraliai/kurpaest/issues](https://github.com/kodokaraliai/kurpaest/issues). One work package per PR unless the issue says otherwise.
