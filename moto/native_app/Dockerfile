# gtk_app/Dockerfile
FROM python:3.12

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system packages including dependencies for PyGObject
RUN apt-get update && \
    apt-get install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    x11-apps \
    gobject-introspection \
    libgirepository1.0-dev \
    libcairo2-dev \
    pkg-config \
    build-essential \
    fonts-inter \
    cmake \
    libglib2.0-dev \
    libffi-dev && \
    apt-get clean

# Set up working directory
WORKDIR /app

# Copy and install the dependencies
COPY requirements.txt .

# Try an alternative approach: use the system PyGObject
RUN pip install --upgrade pip && \
    pip install --no-cache-dir requests watchdog && \
    echo "PyGObject is provided by the system package python3-gi"

# Copy the rest of the application code
COPY . .

# Start the application
CMD ["python3", "dev.py"]