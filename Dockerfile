FROM python:3.11.4-alpine3.17

WORKDIR /app

# Timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Python environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Seoul

RUN apk update && apk add --no-cache git mariadb-dev gcc musl-dev curl build-base libffi-dev openssl-dev python3-dev

COPY  ./pyproject.toml poetry.lock /app/

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

COPY ./app /app/app

EXPOSE 8000
