FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml .
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . .

RUN apt-get update && apt-get install -y curl

CMD ["poetry", "run", "python", "main.py"]
