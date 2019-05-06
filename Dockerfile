FROM python:3.7

WORKDIR /usr/src/app

COPY container_requirements.txt main.py ./
COPY ./server ./server

RUN pip install --no-cache-dir -r container_requirements.txt

CMD ["python", "-OO", "main.py"]
