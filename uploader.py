#! /usr/bin/env python3

'''
Created on Aug 8, 2015

@author: cthulhu
'''
import sys
from oauth2client.client import SignedJwtAssertionCredentials
from httplib2 import Http
import json
from googleapiclient import http
from googleapiclient.discovery import build
import os

def getAuthHttp(config):
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

    media = http.MediaFileUpload(filename, resumable = True, mimetype = config["mimetype"])
    client = build('storage', 'v1', http = getAuthHttp(config))
    req = client.objects().insert(bucket = bucket, name = os.path.basename(filename), media_body = media)
    try:
        req.execute()
    except Exception as e:
        sys.stderr.write("Upload failed! " + repr(e))
        return 1
    return 0

def downloadBucket(bucket, config):
    client = build('storage', 'v1', http = getAuthHttp(config))

    req = client.objects().list(bucket = bucket, fields = "nextPageToken,items(name)", maxResults = 100)
    while req is not None:
        resp = req.execute()
        for item in resp['items']:
            print("Downloading " + item['name'] + "...")
            req = client.objects().get_media(bucket = bucket, object = item['name'])
            fh = open(item['name'], 'w+b')
            downloader = http.MediaIoBaseDownload(fh, req)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print("\tprogress: %.2f%%" % (100 * status.progress()), end = "\r")
            print("")

def main():
    if len(sys.argv) < 3:
        print("Usage: <bucket> <filename> [<config>]")
        return 1
    config = json.loads(open("uploader.json" if len(sys.argv) == 3 else sys.argv[3], "rt").read())
    if sys.argv[1] == "download":
        return downloadBucket(sys.argv[2], config)
    else:
        return upload(sys.argv[1], sys.argv[2], config)

if __name__ == '__main__':
    sys.exit(main())
