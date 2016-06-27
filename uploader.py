#! /usr/bin/env python3

"""
Created on Aug 8, 2015

@author: cthulhu
"""
import sys
from oauth2client.client import SignedJwtAssertionCredentials
from httplib2 import Http
import json
from googleapiclient import http
from googleapiclient.discovery import build
import os


def get_auth_http(config):
    if "private_key" in config:
        private_key = config["private_key"].encode("UTF-8")
    else:
        private_key = open(config["private_key_file"], "rb").read()

    if "scope" not in config:
        config["scope"] = "https://www.googleapis.com/auth/devstorage.read_write"

    credentials = SignedJwtAssertionCredentials(config["email"], private_key, config["scope"])
    return credentials.authorize(Http())


def upload(bucket, filename, config):
    if "mimetype" not in config:
        config["mimetype"] = None

    media = http.MediaFileUpload(filename, resumable=True, mimetype=config["mimetype"])
    client = build("storage", "v1", http=get_auth_http(config))
    req = client.objects().insert(bucket=bucket, name=os.path.basename(filename), media_body=media)
    try:
        req.execute()
    except Exception as e:
        sys.stderr.write("Upload failed! " + repr(e))
        return 1
    return 0


def download_bucket(bucket, config):
    client = build("storage", "v1", http=get_auth_http(config))

    req = client.objects().list(bucket=bucket, fields="nextPageToken,items(name)", maxResults=100)
    while req is not None:
        resp = req.execute()
        for item in resp["items"]:
            download_bucket_file(bucket, item["name"], config, client)
        req = client.objects().list_next(req, resp)


def download_bucket_file(bucket, filename, config, client=None):
    if client is None:
        client = build("storage", "v1", http=get_auth_http(config))
    print("Downloading %s..." % filename)
    req = client.objects().get_media(bucket=bucket, object=filename)
    with open(filename, "w+b") as file:
        downloader = http.MediaIoBaseDownload(file, req)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print("\tprogress: %.2f%%" % (100 * status.progress()), end="\r")
    print("")


def clean_bucket(bucket, config):
    client = build("storage", "v1", http=get_auth_http(config))

    req = client.objects().list(bucket=bucket, fields="nextPageToken,items(name)", maxResults=100)
    days = set()
    while req is not None:
        resp = req.execute()
        for item in resp["items"]:
            date = item["name"][:10]
            if date not in days:
                days.add(date)
            else:
                client.objects().delete(bucket=bucket, object=item["name"]).execute()
        req = client.objects().list_next(req, resp)


def main():
    min_len = 4 if len(sys.argv) > 1 and sys.argv[1] == "download-file" else 3
    if len(sys.argv) < min_len:
        print("Usage: <bucket> <filename> [<config>]"
              " | download <bucket> [<config>]"
              " | download-file <bucket> <file> [<config>]"
              " | clean <bucket> [<config>]")
        return 1
    config = json.loads(open("uploader.json" if len(sys.argv) == min_len else sys.argv[min_len], "rt").read())
    if sys.argv[1] == "download":
        return download_bucket(sys.argv[2], config)
    elif sys.argv[1] == "download-file":
        return download_bucket_file(sys.argv[2], sys.argv[3], config)
    elif sys.argv[1] == "clean":
        return clean_bucket(sys.argv[2], config)
    else:
        return upload(sys.argv[1], sys.argv[2], config)


if __name__ == "__main__":
    sys.exit(main())
