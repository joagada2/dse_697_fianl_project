# Use an official lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory inside the container
RUN mkdir /app
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI app code
COPY . /app/

# Expose the port FastAPI will run on
EXPOSE 80

# Run the Uvicorn server, pointing to app.py's "app" object
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
