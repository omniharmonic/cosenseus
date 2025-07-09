FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download required NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"

# Download spaCy English model (optional - can be done at runtime)
RUN python -m spacy download en_core_web_sm || echo "spaCy model download failed - will fallback at runtime"

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 nlpuser && chown -R nlpuser:nlpuser /app
USER nlpuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"] 