FROM python:3.11.3-slim-bullseye

# Create a non-root user for security with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Create app directory
WORKDIR /app

# Copy application files to the app directory
COPY . .

# Set ownership to the appuser
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# install dependencies from the locked/frozen dependencies file.
RUN pip install --user -r requirements_frozen.txt

CMD ["python", "-m", "pytest", "-vx", "."]


