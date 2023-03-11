FROM python:3.11.2-slim-buster
WORKDIR /usr/src/cirrus
COPY cirrus/server/requirements.txt ./
RUN pip install ruff==0.0.254
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001"]