FROM ubuntu:22.04

ENV TZ Asia/Japan

RUN apt-get update && apt-get install -y python3 python3-pip git

# 设置工作目录
WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN git config --global http.sslVerify false && \
    pip --trusted-host pypi.python.org --trusted-host github.com --trusted-host objects.githubusercontent.com install -r requirements.txt && \
    mkdir -p /app/reports && \
    chown -R 1000:1000 /app/reports

COPY . /app

CMD ["python3", "start.py"]