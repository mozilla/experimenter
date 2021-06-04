FROM nginx:1.19.8

ARG nginx_conf=nginx.conf

RUN rm /etc/nginx/nginx.conf
COPY $nginx_conf /etc/nginx/nginx.conf

COPY key.pem /etc/nginx/
COPY cert.pem /etc/nginx/
