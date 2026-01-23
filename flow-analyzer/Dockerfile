FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml .
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . .

CMD ["poetry", "run", "python", "analyze_flows.py"]
