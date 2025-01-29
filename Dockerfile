FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install psycopg2-binary

COPY . .

CMD ["python", "main.py"]
