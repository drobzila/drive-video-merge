from moviepy.editor import VideoFileClip, concatenate_videoclips
import os

# المجلد الذي يحتوي الفيديوهات
video_folder = "videos"
local_files = [os.path.join(video_folder, f) for f in sorted(os.listdir(video_folder)) if f.endswith(".mp4")]

# الحصول على حجم الفيديو الأول كمرجع
first_clip = VideoFileClip(local_files[0])
target_width, target_height = first_clip.size

# قائمة لتخزين الفيديوهات بعد ضبط الحجم
resized_clips = []

for vf in local_files:
    clip = VideoFileClip(vf)
    # ضبط الحجم إذا كان مختلفًا
    if clip.size != (target_width, target_height):
        clip = clip.resize((target_width, target_height))
    resized_clips.append(clip)

# دمج الفيديوهات مع fade-in/out بسيطة بين كل فيديو
final_clips = []
for i, clip in enumerate(resized_clips):
    if i != 0:
        # إضافة fade-in 1 ثانية للفيديو الحالي
        clip = clip.crossfadein(1)
    final_clips.append(clip)

# دمج كل الفيديوهات
final_video = concatenate_videoclips(final_clips, method="compose")

# حفظ الفيديو النهائي
final_video.write_videofile("final_merged.mp4", codec="libx264", audio_codec="aac", threads=4, verbose=True)
