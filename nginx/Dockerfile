FROM openresty/openresty:trusty

RUN apt-get update
RUN apt-get install -y libssl-dev git-core
RUN luarocks install lua-resty-session
RUN luarocks install lua-resty-openidc

RUN rm /usr/local/openresty/nginx/conf/nginx.conf
COPY nginx.conf /usr/local/openresty/nginx/conf/

COPY openidc.lua /usr/local/openresty/luajit/share/lua/5.1/resty/openidc.lua

COPY openidc_layer.lua /usr/local/openresty/nginx/conf/
COPY login_conf.lua /usr/local/openresty/nginx/conf/
