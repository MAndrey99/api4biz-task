FROM python:3.7

WORKDIR /usr/src/app

COPY requirements.txt .
COPY main.py .
COPY ./server ./server

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
