FROM python:3.7

WORKDIR /usr/src/app

COPY container_requirements.txt .
COPY main.py .
COPY ./server ./server
COPY ./static ./static

RUN pip install --no-cache-dir -r container_requirements.txt

CMD ["python", "main.py"]
