# Google Drive Archive

A Python tool to identify and archive orphaned files in Google Drive.

## Overview

This tool helps you clean up your Google Drive by finding and archiving "orphaned" files - files that are not located in any folder. These files often accumulate over time when files are removed from folders without being deleted, or when shared folders are unshared.

## What are Orphaned Files?

Orphaned files are files in your Google Drive that:
- Have no parent folder (not located in any directory)
- Are owned by you
- Are not in trash

These files typically occur when:
- Files are removed from folders but not deleted
- Shared folders are removed, leaving files behind
- Files are created at the root level without a folder
- Folder structures are reorganized and files are left behind

## Features

- **Safe Operation**: Files are moved to trash (not permanently deleted) and can be restored within 30 days
- **User Confirmation**: Displays the list of orphaned files and requires confirmation before archiving
- **OAuth2 Authentication**: Secure authentication using Google's OAuth2 flow
- **Pagination Support**: Efficiently handles large Google Drive accounts
- **Graceful Interruption**: Supports Ctrl+C to exit cleanly at any time

## Prerequisites

- Python 3.7 or higher
- A Google account with Google Drive
- Google Cloud Console project with Drive API enabled

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/gdrive-archive.git
   cd gdrive-archive
   ```

2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### 1. Enable Google Drive API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### 2. Create OAuth2 Credentials

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure the OAuth consent screen if prompted
4. Select "Desktop app" as the application type
5. Give it a name (e.g., "gdrive-archive")
6. Click "Create"
7. Download the JSON file

### 3. Install Credentials

Copy the downloaded `client_secret.json` file to:
```
~/.credentials/gdrive-archive/client_secret.json
```

Create the directory if it doesn't exist:
```bash
mkdir -p ~/.credentials/gdrive-archive
cp /path/to/downloaded/client_secret_*.json ~/.credentials/gdrive-archive/client_secret.json
```

## Usage

Run the script:
```bash
python gdrive_archive.py
```

The script will:
1. Open your browser for Google authentication (first run only)
2. Search your Google Drive for orphaned files
3. Display the count of orphaned files found
4. List each orphaned file name
5. Wait for you to press Enter to confirm
6. Archive (trash) the files

### Command-line Options

- `--noauth_local_webserver`: Use this flag if running on a remote/headless server. It will provide a URL for you to visit for authentication.

Example:
```bash
python gdrive_archive.py --noauth_local_webserver
```

## How It Works

1. **Authentication**: Uses OAuth2 to securely access your Google Drive
2. **Search**: Queries all files in your Drive (excluding trash) and filters for:
   - Files with no parent folder
   - Files owned by you
3. **Review**: Shows you the list of orphaned files
4. **Archive**: After confirmation, moves files to trash using the Drive API

## Safety Notes

- **Non-destructive**: Files are moved to trash, not permanently deleted
- **Recoverable**: Trashed files can be restored from Google Drive trash for 30 days
- **User-controlled**: Requires explicit confirmation before archiving
- **Read-only until confirmed**: No changes are made until you press Enter to confirm

## Troubleshooting

### "File not found: client_secret.json"
Make sure you've placed the OAuth2 credentials file at:
`~/.credentials/gdrive-archive/client_secret.json`

### Authentication Issues
Delete the stored token and re-authenticate:
```bash
rm ~/.credentials/gdrive-archive/user_token.json
python gdrive_archive.py
```

### No Orphaned Files Found
If the script reports 0 orphaned files, your Drive is already well-organized! All your files are in folders.

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
