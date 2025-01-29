FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && \
    apt-get install -y pkg-config libmariadb-dev-compat libmariadb-dev gcc && \
    apt-get clean

COPY . .

CMD ["python", "main.py"]