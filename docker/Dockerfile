#Use base image
FROM python:3.11-slim

#Set working directory
WORKDIR /app

#Copy the porject code
COPY . .

#Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

#Expose the FastAPI port
EXPOSE 8000

# Run migrations + seed + start server
CMD ["sh", "-c","alembic upgrade head && python seed.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
