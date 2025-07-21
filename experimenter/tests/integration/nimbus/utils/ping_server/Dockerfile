FROM python:3.10

COPY ping_server.py /code/

WORKDIR /code

RUN pip install flask

ENTRYPOINT [ "python" ]

CMD [ "ping_server.py" ]