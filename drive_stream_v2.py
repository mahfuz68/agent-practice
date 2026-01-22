#!/usr/bin/env python3
"""
Google Drive Direct Link Generator with Virus Scan Bypass

This script handles Google Drive's virus scan warning for large files
and generates working direct download links for VLC streaming.
"""

import os
import sys
import re
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Google Drive configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

def authenticate_google_drive():
    """Authenticate with Google Drive API"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ Error: {CREDENTIALS_FILE} not found!")
                print("Please download credentials.json from Google Cloud Console")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def get_real_download_link(file_id):
    """Get the real download link by handling virus scan warning"""
    try:
        # First, try the standard link
        url = f"https://drive.google.com/uc?export=download&id={file_id}"

        # Check if we get the virus scan warning
        response = requests.get(url, allow_redirects=True, timeout=10)

        if "Virus scan warning" in response.text:
            print("🔍 Detected virus scan warning, extracting confirmation parameters...")

            # Extract the confirmation parameters from the HTML
            confirm_match = re.search(r'name="confirm"\s+value="([^"]+)"', response.text)
            uuid_match = re.search(r'name="uuid"\s+value="([^"]+)"', response.text)

            if confirm_match and uuid_match:
                confirm = confirm_match.group(1)
                uuid = uuid_match.group(1)

                # Generate the real download URL
                real_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm={confirm}&uuid={uuid}"
                return real_url
            else:
                print("❌ Could not extract confirmation parameters")
                return None
        else:
            # No virus scan warning, return the standard URL
            return url

    except Exception as e:
        print(f"❌ Error getting download link: {str(e)}")
        return None

def get_direct_link(file_id):
    """Get direct download link for Google Drive file"""
    try:
        drive_service = authenticate_google_drive()

        # Get file metadata
        file_metadata = drive_service.files().get(
            fileId=file_id,
            fields='name,mimeType,size,webContentLink,webViewLink'
        ).execute()

        filename = file_metadata.get('name', 'Unknown')
        mime_type = file_metadata.get('mimeType', 'Unknown')
        file_size = file_metadata.get('size', 'Unknown')

        # Check file permissions
        permissions = drive_service.permissions().list(fileId=file_id).execute()
        is_public = any(p.get('type') == 'anyone' and p.get('role') in ['reader', 'writer'] for p in permissions.get('permissions', []))

        # Get the real download link (handling virus scan)
        real_download_link = get_real_download_link(file_id)

        print("🎵 Google Drive Direct Link Generator")
        print("=" * 50)
        print(f"📄 File Name: {filename}")
        print(f"🎯 MIME Type: {mime_type}")
        print(f"📏 File Size: {file_size} bytes")
        print(f"🔓 Public Access: {'Yes' if is_public else 'No (Private)'}")
        print()
        print("🔗 Direct Download Links:")

        if real_download_link:
            print(f"VLC Stream: {real_download_link}")
            print("✅ This link should work for streaming!")
        else:
            print("❌ Could not generate working download link")

        print()
        print("💡 How to stream in VLC:")
        print("1. Copy the VLC Stream link above")
        print("2. Open VLC Media Player")
        print("3. Media → Open Network Stream")
        print("4. Paste the link and click Play")
        print()
        print("⚠️  Note: Large files may show virus scan warnings from Google")
        print("   This script automatically handles those warnings.")

        return real_download_link

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python drive_stream_v2.py <file_id>")
        print("Example: python drive_stream_v2.py 1ABC123xyz456DEF789")
        sys.exit(1)

    file_id = sys.argv[1]
    get_direct_link(file_id)

if __name__ == "__main__":
    main()