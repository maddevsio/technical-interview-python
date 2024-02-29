FROM python:3.10-slim as base

# Create the application directory
WORKDIR /app

# Copy project and common files into image
COPY . .

# Install python package manager
RUN pip install poetry

# Install production python dependencies
RUN poetry install

# Specify application entrypoint for docker run
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
