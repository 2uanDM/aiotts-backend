FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install Python dependencies (Since docker will check for changes in the requirements.txt file, it will only install the dependencies if there are any changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 1234

# Launch server
CMD uvicorn app.main:app --host 0.0.0.0 --port 1234
