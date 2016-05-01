FROM debian:jessie

RUN apt-get update && apt-get install -y python3 python3-pip python3-six openssl python3-openssl \
        && pip3 install "oauth2client>1.5,<1.99" "google-api-python-client>1.4,<1.4.99" \
        && apt-get purge -y python3-pip && apt-get autoremove -y

WORKDIR /app
COPY . .

ENTRYPOINT ["./uploader.py"]
