FROM nginx:1.9.9

RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx-site.conf /etc/nginx/conf.d/
