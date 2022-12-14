FROM python:3.8-alpine

EXPOSE 8000

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD python ./main.py