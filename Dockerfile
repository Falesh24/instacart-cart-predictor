# Use a lightweight, optimized Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency mappings and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire local project codebase over to the container
COPY . .

# Expose the production port our FastAPI app runs on
EXPOSE 8080

# Command to boot up the microservice inside the container environment
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
