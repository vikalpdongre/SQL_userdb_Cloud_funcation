# Use a slim Python image as the base
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This is done separately to leverage Docker's layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container
COPY . .

# Expose the port that Flask will run on (default for Flask is 5000)
EXPOSE 5000

# Define the command to run the Flask application
# Use Gunicorn for production-ready deployment
# You'll need to install gunicorn in your requirements.txt
# CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"] # Assuming your Flask app instance is named 'app' in 'app.py'

# For development purposes, you can use Flask's built-in server (less robust)
CMD ["python", "app.py"]
