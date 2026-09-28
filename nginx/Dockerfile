FROM nginx:1.31.6

RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/

COPY key.pem /etc/nginx/
COPY cert.pem /etc/nginx/
