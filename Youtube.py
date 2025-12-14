import os
import subprocess
import io
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ================== SETTINGS ==================
FOLDER_ID = "1ZGX6heziORR_6JUjXB-o7qCHiJQgAgyT"
OUTPUT_VIDEO = "final_merged.mp4"
TRANSITION_DURATION = 1  # seconds
SERVICE_ACCOUNT_JSON = json.loads(os.environ["GDRIVE_SERVICE_ACCOUNT"])

creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_JSON,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
# ==============================================

# Check FFmpeg exists
if not os.path.isfile(FFMPEG_PATH):
    raise FileNotFoundError(f"FFmpeg not found at {FFMPEG_PATH}")

# Create workspace
os.makedirs("videos", exist_ok=True)

# Authenticate
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
service = build('drive', 'v3', credentials=creds)

# List videos in folder
results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    fields="files(id, name, mimeType)"
).execute()
files = sorted(results.get('files', []), key=lambda x: x['name'])

# Filter supported video types
local_files = []
for i, file in enumerate(files):
    if not file['name'].lower().endswith(('.mp4', '.mov', '.mkv')):
        continue

    request = service.files().get_media(fileId=file['id'])
    fh = io.FileIO(f"videos/{i}.mp4", 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    local_files.append(f"videos/{i}.mp4")

if not local_files:
    print("❌ No video files found in the Drive folder. Make sure the folder is shared with the Service Account.")
    exit(1)

print(f"✅ Downloaded {len(local_files)} video(s)")

# Build FFmpeg filter_complex with transitions (xfade)
filter_parts = []
input_parts = []
for i, vf in enumerate(local_files):
    input_parts.append(f"-i {vf}")

offset = 0
for i in range(len(local_files) - 1):
    filter_parts.append(
        f"[{i}:v][{i+1}:v]xfade=transition=fade:duration={TRANSITION_DURATION}:offset={offset}[v{i+1}]"
    )
    offset += TRANSITION_DURATION

filter_complex = ";".join(filter_parts)

if not filter_complex:
    print("❌ Not enough videos to create transitions. At least 2 videos are required.")
    exit(1)

cmd = f'"{FFMPEG_PATH}" {' '.join(input_parts)} -filter_complex "{filter_complex}" -map "[v{len(local_files)-1}]" -y {OUTPUT_VIDEO}'

print("🎬 Running FFmpeg...")
subprocess.run(cmd, shell=True, check=True)

print("✅ Final video created:", OUTPUT_VIDEO)

