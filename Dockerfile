FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
#ENV FLASK_APP=app.py ENV FLASK_ENV=production ENV JWT_SECRET_KEY=your-secret-key
EXPOSE 5000
CMD ["python","app.py"]
