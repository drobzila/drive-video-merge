import os
import subprocess
import io
import json
from moviepy.editor import VideoFileClip
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# ================== SETTINGS ==================
FOLDER_ID = "1ZGX6heziORR_6JUjXB-o7qCHiJQgAgyT"
OUTPUT_VIDEO = "final_merged.mp4"
TRANSITION_DURATION = 1  # seconds
FFMPEG_PATH = "/usr/bin/ffmpeg"
VIDEO_DIR = "videos"
# ==============================================

# Authenticate using GitHub Secret
SERVICE_ACCOUNT_JSON = json.loads(os.environ["GDRIVE_SERVICE_ACCOUNT"])
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_JSON,
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build('drive', 'v3', credentials=creds)

# Create workspace
os.makedirs(VIDEO_DIR, exist_ok=True)

# List videos in Drive folder
results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    fields="files(id, name, mimeType)"
).execute()
files = sorted(results.get('files', []), key=lambda x: x['name'])

# Download video files
local_files = []
for i, file in enumerate(files):
    if not file['name'].lower().endswith(('.mp4', '.mov', '.mkv')):
        continue

    request = service.files().get_media(fileId=file['id'])
    fh = io.FileIO(f"{VIDEO_DIR}/{i}.mp4", 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    local_files.append(f"{VIDEO_DIR}/{i}.mp4")

if len(local_files) < 2:
    print("❌ Not enough videos for transitions. At least 2 required.")
    exit(1)

print(f"✅ Downloaded {len(local_files)} video(s)")

# Resize all videos to the size of the first clip
first_clip = VideoFileClip(local_files[0])
target_width, target_height = first_clip.size

resized_files = []
for i, vf in enumerate(local_files):
    clip = VideoFileClip(vf)
    if clip.size != (target_width, target_height):
        resized_path = f"{VIDEO_DIR}/resized_{i}.mp4"
        clip.resize(height=target_height, width=target_width).write_videofile(
            resized_path, codec="libx264", audio_codec="aac", verbose=False, logger=None
        )
        resized_files.append(resized_path)
    else:
        resized_files.append(vf)

# Build FFmpeg filter_complex for sequential xfade transitions
filter_parts = []
input_parts = []
offset = 0

for vf in resized_files:
    input_parts.append(f"-i {vf}")

for i in range(len(resized_files) - 1):
    if i == 0:
        filter_parts.append(
            f"[0:v][1:v]xfade=transition=fade:duration={TRANSITION_DURATION}:offset={offset}[v{i+1}]"
        )
    else:
        filter_parts.append(
            f"[v{i}][{i+1}:v]xfade=transition=fade:duration={TRANSITION_DURATION}:offset={offset}[v{i+1}]"
        )
    clip = VideoFileClip(resized_files[i])
    offset += clip.duration - TRANSITION_DURATION

filter_complex = ";".join(filter_parts)
cmd = f'{FFMPEG_PATH} {" ".join(input_parts)} -filter_complex "{filter_complex}" -map "[v{len(resized_files)-1}]" -y {OUTPUT_VIDEO}'

print("🎬 Running FFmpeg...")
subprocess.run(cmd, shell=True, check=True)
print(f"✅ Final video created: {OUTPUT_VIDEO}")

# Upload final video to Drive
file_metadata = {'name': OUTPUT_VIDEO, 'parents': [FOLDER_ID]}
media = MediaFileUpload(OUTPUT_VIDEO, mimetype='video/mp4')
uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
print(f"✅ Video uploaded to Drive with file ID: {uploaded_file.get('id')}")

