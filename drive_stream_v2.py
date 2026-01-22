#!/usr/bin/env python3
"""
Google Drive Direct Link Generator with Virus Scan Bypass

This script handles Google Drive's virus scan warning for large files
and generates working direct download links for VLC streaming.
Supports both individual files and folders (generates M3U playlists for video folders).
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

def extract_id_from_url(url):
    """Extract file or folder ID from Google Drive URL"""
    # Match file URL: https://drive.google.com/file/d/{id}/view?usp=drive_link
    file_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if file_match:
        return 'file', file_match.group(1)
    
    # Match folder URL: https://drive.google.com/drive/folders/{id}?usp=drive_link
    folder_match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
    if folder_match:
        return 'folder', folder_match.group(1)
    
    # Fallback: assume it's a direct ID
    return 'file', url

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

def process_folder(folder_id):
    """Process a Google Drive folder and generate M3U playlist for video files"""
    try:
        drive_service = authenticate_google_drive()

        # Get folder metadata
        folder_metadata = drive_service.files().get(
            fileId=folder_id,
            fields='name'
        ).execute()
        folder_name = folder_metadata.get('name', 'Unknown_Folder')

        # List video files in the folder
        query = f"'{folder_id}' in parents and mimeType contains 'video/'"
        results = drive_service.files().list(
            q=query,
            fields="files(id,name,mimeType)"
        ).execute()
        video_files = results.get('files', [])

        if not video_files:
            print(f"❌ No video files found in folder '{folder_name}'")
            return

        print(f"📁 Processing folder: {folder_name}")
        print(f"🎥 Found {len(video_files)} video files")

        # Generate M3U content
        m3u_content = "#EXTM3U\n"
        for video in video_files:
            file_id = video['id']
            filename = video['name']
            direct_link = get_real_download_link(file_id)
            if direct_link:
                m3u_content += f"#EXTINF:-1,{filename}\n{direct_link}\n"
            else:
                print(f"⚠️  Could not generate link for {filename}")

        # Ensure v_link directory exists
        v_link_dir = 'v_link'
        if not os.path.exists(v_link_dir):
            os.makedirs(v_link_dir)

        # Write M3U file
        m3u_filename = f"{folder_name}.m3u"
        m3u_path = os.path.join(v_link_dir, m3u_filename)
        with open(m3u_path, 'w', encoding='utf-8') as f:
            f.write(m3u_content)

        print(f"✅ M3U playlist generated: {m3u_path}")
        print("💡 You can open this file in VLC Media Player to stream all videos")

    except Exception as e:
        print(f"❌ Error processing folder: {str(e)}")

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

        return real_download_link

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python drive_stream_v2.py <Google Drive URL or File/Folder ID>")
        print("Examples:")
        print("  python drive_stream_v2.py https://drive.google.com/file/d/1ABC123xyz456DEF789/view?usp=drive_link")
        print("  python drive_stream_v2.py https://drive.google.com/drive/folders/1-7IK1sZ_vqphG6L8zr7DOpPcUGwkLQnC?usp=drive_link")
        print("  python drive_stream_v2.py 1ABC123xyz456DEF789")
        sys.exit(1)

    input_url = sys.argv[1]
    link_type, item_id = extract_id_from_url(input_url)

    if link_type == 'folder':
        process_folder(item_id)
    else:
        get_direct_link(item_id)

if __name__ == "__main__":
    main()