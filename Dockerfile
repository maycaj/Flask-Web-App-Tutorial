# Use the official Python image as a base
FROM python:3.8-slim

# Set the working directory
WORKDIR /app/website

# Copy the application code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port where your Flask app listens (usually 5000)
EXPOSE 8080

# Command to run the Flask app
CMD ["flask", "run"]