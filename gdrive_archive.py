"""Google Drive Archive Tool

This script identifies and archives "orphaned" files in Google Drive - files that
are not located in any folder (have no parent) and are owned by the current user.

Orphaned files typically occur when:
- Files are removed from folders but not deleted
- Shared folders are removed, leaving files behind
- Files are created outside of any folder structure

The script performs the following operations:
1. Authenticates with Google Drive API using OAuth2
2. Searches for all untrashed files without parent folders owned by you
3. Displays the list of orphaned files found
4. After user confirmation, moves these files to trash (archives them)

Prerequisites:
- Python 3.7+
- Google Drive API enabled in Google Cloud Console
- client_secret.json file from Google Cloud Console

Usage:
    python gdrive_archive.py [--noauth_local_webserver]

The --noauth_local_webserver flag is useful for remote/headless environments.
"""

from __future__ import print_function

import argparse
import os
import signal
import sys
from argparse import Namespace

import httplib2
from googleapiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage

# Google Drive API configuration
SCOPES = "https://www.googleapis.com/auth/drive"  # Full Drive access scope
CLIENT_SECRET_FILE = "client_secret.json"  # OAuth2 client secret filename
APPLICATION_NAME = "gdrive-archive"  # Application identifier
USER_AGENT = "Google Drive Archive"  # User agent for API requests

# Parse command-line arguments (includes OAuth2 flags like --noauth_local_webserver)
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
    """Get valid user credentials from storage.

    Retrieves OAuth2 credentials for Google Drive API access. If credentials
    don't exist or are invalid, initiates the OAuth2 flow to obtain new ones.

    Credentials are stored in ~/.credentials/gdrive-archive/ directory:
    - user_token.json: Stores the OAuth2 access token
    - client_secret.json: OAuth2 client configuration (must be provided by user)

    Returns:
        OAuth2Credentials: Valid credentials for Google Drive API access.

    Raises:
        FileNotFoundError: If client_secret.json is not found in the credentials directory.
    """
    # Create credentials directory structure if it doesn't exist
    credential_dir = os.path.join(os.path.expanduser("~"), ".credentials")
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    app_dir = os.path.join(credential_dir, APPLICATION_NAME)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

    # Load existing credentials or initiate OAuth2 flow if needed
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
    """Get all orphaned files from Google Drive.

    Searches through all files in Google Drive to find orphaned files - files
    that meet the following criteria:
    - Not in trash (trashed=false)
    - No parent folder (parents field is empty/null)
    - Owned by the current user (me=true in owners)

    Uses pagination to handle large Drive contents efficiently.

    Args:
        service: Authorized Google Drive API service instance.

    Returns:
        list: List of file dictionaries containing id, name, parents, and owners fields.
    """
    files = []
    next_page = None

    # Paginate through all files in Drive
    while True:
        results = (
            service.files()
            .list(
                q="trashed=false",  # Only non-trashed files
                spaces="drive",
                pageSize=1000,  # Maximum page size
                fields="nextPageToken, files(id, name, parents, owners)",
                pageToken=next_page,
            )
            .execute()
        )
        items = results.get("files", [])
        if not items:
            break

        # Filter for orphaned files owned by the user
        for item in items:
            if not item.get("parents"):  # File has no parent folder
                if "owners" in item and item["owners"][0]["me"]:  # User owns the file
                    files.append(item)

        next_page = results.get("nextPageToken")
        if not next_page:
            break
    return files


def archive_files(service, files):
    """Archive a list of files by moving them to trash.

    Iterates through the provided files and moves each one to trash by
    setting the 'trashed' property to True. Prints each file name as it's
    being archived.

    Note: Files are moved to trash, not permanently deleted. They can be
    restored from the Google Drive trash within 30 days.

    Args:
        service: Authorized Google Drive API service instance.
        files: List of file dictionaries with 'id' and 'name' fields.
    """
    for file in files:
        print(file["name"])
        # Move file to trash (can be restored within 30 days)
        service.files().update(fileId=file["id"], body={"trashed": True}).execute()


def main():
    """Main entry point for the Google Drive archive tool.

    Performs the complete workflow:
    1. Sets up signal handler for graceful interruption (Ctrl+C)
    2. Authenticates with Google Drive API
    3. Searches for orphaned files
    4. Displays count of orphaned files found
    5. Waits for user confirmation
    6. Archives (trashes) the orphaned files
    """
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Authenticate and build Drive API service
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive", "v3", http=http)

    # Find all orphaned files
    files = get_files(service)
    print(f"Found {len(files)} orphan file(s)")

    # Only proceed if orphaned files were found
    if files:
        input("Press Enter to continue...")
        archive_files(service, files)


if __name__ == "__main__":
    main()
