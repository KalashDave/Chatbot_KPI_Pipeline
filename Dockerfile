# Use the official Python 3.12 slim image to keep the container lightweight
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency requirements file into the container
COPY requirements.txt .

# Install the Python dependencies (no cache to save space)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the application files (code, assets, database) into the container
COPY . .

# Expose port 8050, which is the port Dash uses
EXPOSE 8050

# The command to boot up the high-performance Gunicorn web server
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "src.dash_app:server"]
