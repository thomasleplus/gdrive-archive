"""Module to archive orphaned Google Drive files."""

from __future__ import print_function

import argparse
import os
import signal
import sys

import httplib2
from googleapiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage

SCOPES = "https://www.googleapis.com/auth/drive"
CLIENT_SECRET_FILE = "client_secret.json"
APPLICATION_NAME = "gdrive-archive"
USER_AGENT = "Google Drive Archive"

try:
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    ARGS: Namespace | None = parser.parse_args()
except ImportError:
    ARGS = None


def signal_handler(_signal, _frame):
    """Handle SIGINT."""
    print("")
    sys.exit(0)


def get_credentials():
    """Get valid user credentials from storage."""
    credential_dir = os.path.join(os.path.expanduser("~"), ".credentials")
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    app_dir = os.path.join(credential_dir, APPLICATION_NAME)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    token_path = os.path.join(app_dir, "user_token.json")
    store = Storage(token_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        secret_path = os.path.join(app_dir, "client_secret.json")
        flow = client.flow_from_clientsecrets(secret_path, SCOPES)
        flow.user_agent = USER_AGENT
        if ARGS:
            credentials = tools.run_flow(flow, store, ARGS)
        else:
            credentials = tools.run(flow, store)
    return credentials


def get_files(service):
    """Get all orphaned files from Google Drive."""
    files = []
    next_page = None
    while True:
        results = (
            service.files()
            .list(
                q="trashed=false",
                spaces="drive",
                pageSize=1000,
                fields="nextPageToken, files(id, name, parents, owners)",
                pageToken=next_page,
            )
            .execute()
        )
        items = results.get("files", [])
        if not items:
            break

        for item in items:
            if not item.get("parents"):
                if "owners" in item and item["owners"][0]["me"]:
                    files.append(item)

        next_page = results.get("nextPageToken")
        if not next_page:
            break
    return files


def archive_files(service, files):
    """Archive a list of files."""
    for file in files:
        print(file["name"])
        service.files().update(fileId=file["id"], body={"trashed": True}).execute()


def main():
    """Archive orphaned Google Drive files."""
    signal.signal(signal.SIGINT, signal_handler)
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive", "v3", http=http)
    files = get_files(service)
    print(f"Found {len(files)} orphan file(s)")
    if files:
        input("Press Enter to continue...")
        archive_files(service, files)


if __name__ == "__main__":
    main()
