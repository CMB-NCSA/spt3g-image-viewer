FROM python:3.12 AS deps

RUN pip install --upgrade pip
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt --no-cache-dir

FROM python:3.12

COPY --from=deps /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

RUN mkdir /app
COPY . /app
WORKDIR /app
