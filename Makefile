test:
	pytest

format:
	ruff format masstransit/
	ruff check masstransit/ --fix

lint:
	mypy masstransit
