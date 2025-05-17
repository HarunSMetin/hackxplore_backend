FROM python:3.11-slim 

# Set working directory
WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary files first (for better caching)
COPY models/ ./models/
COPY schemas/ ./schemas/
COPY crud/ ./crud/
COPY services/ ./services/
COPY database/ ./database/
COPY routes/ ./routes/
COPY scripts/ ./scripts/
COPY main.py init_db.py run.sh ./

# Copy the CSV file (if available)
COPY augmented_common_containers_with_types.csv ./augmented_common_containers_with_types.csv

# Make the run.sh script executable
RUN chmod +x run.sh

# Expose the port
EXPOSE 8000

# Run the application
CMD ["bash", "run.sh"] 