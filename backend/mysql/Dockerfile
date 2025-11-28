FROM mysql:latest

ENV MYSQL_ROOT_PASSWORD=123456

ENV LANG=C.UTF-8

COPY my.cnf /etc/mysql/my.cnf

COPY init.sql /docker-entrypoint-initdb.d/

VOLUME /var/lib/mysql