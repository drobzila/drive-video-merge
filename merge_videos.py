import os
import io
import subprocess
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

FOLDER_ID = "1ZGX6heziORR_6JUjXB-o7qCHiJQgAgyT"
OUTPUT_VIDEO = "final.mp4"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = Credentials.from_service_account_file(
    "credentials.json", scopes=SCOPES
)

service = build("drive", "v3", credentials=creds)

query = f"'{FOLDER_ID}' in parents and mimeType contains 'video/'"
results = service.files().list(q=query, fields="files(id, name)").execute()
files = results.get("files", [])

os.makedirs("videos", exist_ok=True)

local_files = []

for f in files:
    request = service.files().get_media(fileId=f["id"])
    fh = io.FileIO(f"videos/{f['name']}", "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    local_files.append(f"videos/{f['name']}")

# توحيد الحجم تلقائيًا باستخدام FFmpeg
input_parts = []
filter_complex = ""

for i, file in enumerate(local_files):
    input_parts.append(f'-i "{file}"')
    filter_complex += f"[{i}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2[v{i}];"

filter_complex += "".join([f"[v{i}]" for i in range(len(local_files))])
filter_complex += f"concat=n={len(local_files)}:v=1:a=0[outv]"

cmd = f'ffmpeg {" ".join(input_parts)} -filter_complex "{filter_complex}" -map "[outv]" -y {OUTPUT_VIDEO}'

subprocess.run(cmd, shell=True, check=True)

print("✅ تم دمج الفيديوهات بنجاح")

