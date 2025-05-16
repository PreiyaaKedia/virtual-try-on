FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure the uploads and generated_images directories exist
RUN mkdir -p uploads/user_images uploads/user_items generated_images

# Expose the port Streamlit will run on
EXPOSE 8501

# Set Streamlit-specific environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run Streamlit directly (no need for WSGI wrappers)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
