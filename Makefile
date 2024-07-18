test:
	pytest -vv --cov masstransit

format:
	ruff format masstransit/
	ruff check masstransit/ --fix-only

lint:
	ruff check masstransit/
	mypy masstransit
