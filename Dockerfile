# Use an official Python image as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt (or any other dependency management file)
COPY ./app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app .

ENV COLLECTION_EMPLOYEES_NAME="employees"
ENV COLLECTION_SALARY_NAME="salary"
ENV COLLECTION_TIMEKEEPING_NAME="timekeeping"
ENV DB_NAME="dbemp"
ENV MONGODB_URL="mongodb://localhost:27017"
ENV RAILWAY_PROD_URL="https://finalcapstonebackend-production.up.railway.app/"
ENV MONGODB_URLCLOUD="mongodb+srv://redim:root@cluster0.hdtrrtt.mongodb.net/"
ENV PORT=8000 

# Expose the port the backend will run on
EXPOSE 8000

# Command to run the backend server (adjust for Flask or FastAPI)
CMD python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
