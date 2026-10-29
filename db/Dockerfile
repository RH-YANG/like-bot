FROM postgres:18

ENV TZ=UTC

COPY db/schema.sql /docker-entrypoint-initdb.d/001-schema.sql
