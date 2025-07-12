FROM python:3.11.3-slim-bullseye

# Create a non-root user for security with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Set working directory to user's home
WORKDIR /home/appuser

# Copy application files to the user's home directory
COPY . .

# Set ownership to the appuser
RUN chown -R appuser:appuser /home/appuser

# Switch to the non-root user
USER appuser

# Install dependencies (--user flag not needed since we're already in user's home)
RUN pip install -r requirements_frozen.txt

CMD ["python", "-m", "pytest", "-vx", "."]


