FROM python:3.9
WORKDIR /app            
COPY . .
# Kalıcı olarak sqlite3 yükleniyor:
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
