from moviepy import VideoFileClip, concatenate_videoclips
import os

# مجلد الفيديوهات
video_folder = "videos"
local_files = [os.path.join(video_folder, f) for f in sorted(os.listdir(video_folder)) if f.endswith(".mp4")]

# استخدام أول فيديو كمرجع للحجم
first_clip = VideoFileClip(local_files[0])
target_width, target_height = first_clip.size

clips = []

# تحميل وتعديل حجم الفيديوهات إذا لزم الأمر
for vf in local_files:
    clip = VideoFileClip(vf)
    if clip.size != (target_width, target_height):
        clip = clip.resize((target_width, target_height))
    clips.append(clip)

# إعداد Fade Transition بين الفيديوهات
fade_duration = 1  # مدة الانتقال بالثواني
clips_with_fade = []

for i, clip in enumerate(clips):
    if i > 0:
        clip = clip.crossfadein(fade_duration)
    clips_with_fade.append(clip)

# دمج الفيديوهات
final_video = concatenate_videoclips(clips_with_fade, method="compose")

# حفظ الفيديو النهائي
final_video.write_videofile(
    "final_merged.mp4",
    codec="libx264",
    audio_codec="aac",
    threads=4,
    fps=30  # ضبط FPS لتجنب مشاكل FFmpeg
)
