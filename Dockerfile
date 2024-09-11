FROM python:3 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
COPY Dockerfile /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt