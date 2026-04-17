FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt 

COPY . .

CMD ["sh", "-c", "python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p $PORT core.asgi:application"]
