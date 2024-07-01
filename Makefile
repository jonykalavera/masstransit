test:
	pytest -vv --cov masstransit

format:
	ruff format masstransit/
	ruff check masstransit/ --fix

lint:
	mypy masstransit
