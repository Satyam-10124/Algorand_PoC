FROM node:16 as build-frontend

WORKDIR /app/frontend

# Copy frontend files and install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build React app
RUN npm run build

# Second stage: Python environment
FROM python:3.9

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask app and compiled React files
COPY app.py .
COPY Compliance/ ./Compliance/
COPY --from=build-frontend /app/frontend/build ./frontend/build

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
