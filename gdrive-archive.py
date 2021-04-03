#!/usr/bin/python

from __future__ import print_function
import httplib2
import os
import signal
import sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'gdrive-archive'
USER_AGENT = 'Google Drive Archive'

try:
    import argparse
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    args = parser.parse_args()
except ImportError:
    args = None


def signal_handler(signal, frame):
    print('')
    sys.exit(0)


def get_credentials():
    credential_dir = os.path.join(os.path.expanduser('~'), '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    app_dir = os.path.join(credential_dir, APPLICATION_NAME)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    token_path = os.path.join(app_dir, 'user_token.json')
    store = Storage(token_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        secret_path = os.path.join(app_dir, 'client_secret.json')
        flow = client.flow_from_clientsecrets(secret_path, SCOPES)
        flow.user_agent = USER_AGENT
        if args:
            credentials = tools.run_flow(flow, store, args)
        else:
            credentials = tools.run(flow, store)
    return credentials


def get_files(service):
    files = []
    next_page = None
    while True:
        results = service.files().list(q='trashed=false',
                                       spaces='drive',
                                       pageSize=1000,
                                       fields="nextPageToken, \
                                       files(id, name, parents)",
                                       pageToken=next_page).execute()
        items = results.get('files', [])
        if not items:
            break
        else:
            for file in files:
                if not file['parents'] and len(file['owners']) == 1 \
                   and file['owners'][0]['isAuthenticatedUser']:
                    files.extend(file)
            next_page = results.get('nextPageToken')
        if not next_page:
            break
    return files


def archive_files(service, files):
    for file in files:
        print(file['name'])
        service.files().update(fileId=file['id'], body={'trashed' : True}).execute()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    files = get_files(service)
    print('Found {0} orphan file(s)'.format(len(files)))
    if files:
        raw_input('Press Enter to continue...')
        archive_files(service, files)

if __name__ == '__main__':
    main()
