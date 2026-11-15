# Step 1: Base image
# We use an official, lightweight Python 3.11 slim image
FROM python:3.11-slim

# Step 2: Set environment variables
# PYTHONDONTWRITEBYTECODE prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED ensures stdout and stderr streams are sent straight to terminal/logs without buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Step 3: Set working directory inside the container
WORKDIR /app

# Step 4: Copy dependency list first to leverage Docker layer caching
COPY requirements.txt .

# Step 5: Install Python dependencies
# --no-cache-dir keeps image size minimal by not caching download wheels
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy the application code into the container
COPY . .

# Step 7: Inform Docker that the container listens on port 5000 at runtime
EXPOSE 5000

# Step 8: Command to execute when the container starts
CMD ["python", "app.py"]
