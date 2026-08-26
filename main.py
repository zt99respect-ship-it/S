import os
import sys
import json
import subprocess
import google.generativeai as genai

youtube_url = sys.argv[1]
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

print("[+] جاري تنزيل الفيديو والنص...")
cmd_dl = [
    "yt-dlp",
    "--write-auto-sub",
    "--sub-lang", "ar,en",
    "--convert-subs", "srt",
    "-f", "mp4[height<=720]",
    "-o", "input_video.%(ext)s",
    youtube_url
]
subprocess.run(cmd_dl)

srt_file = next((f for f in os.listdir(".") if f.endswith(".srt")), None)

if not srt_file:
    print("[-] لم يتم العثور على ترجمة تلقائية.")
    sys.exit(1)

with open(srt_file, "r", encoding="utf-8") as f:
    transcript_text = f.read()

print("[+] تحليل المقطع واستخراج أفضل 10 لحظات...")
model = genai.GenerativeModel("gemini-1.5-flash")
prompt = f"""
إليك نص التفريغ الصوتي:
{transcript_text[:10000]}

استخرج أفضل 10 مقاطع قصيرة قادرة على جلب مشاهدات عالية (بين 30 إلى 60 ثانية).
أرجع JSON فقط:
[
  {{"start": "00:01:20", "end": "00:02:00", "title": "short_1"}},
  ...
]
"""

response = model.generate_content(prompt)
clean_json = response.text.strip().replace("```json", "").replace("```", "")
clips = json.loads(clean_json)

os.makedirs("output_shorts", exist_ok=True)

for idx, clip in enumerate(clips, 1):
    start = clip["start"]
    end = clip["end"]
    output_path = f"output_shorts/short_{idx}.mp4"
    
    vf_filter = (
        f"crop=ih*(9/16):ih,"
        f"subtitles='{srt_file}':force_style='Alignment=2,FontSize=20,PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BorderStyle=3'"
    )
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-ss", start,
        "-to", end,
        "-i", "input_video.mp4",
        "-vf", vf_filter,
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(ffmpeg_cmd)
    print(f"[✓] تم إنشاء المقطع: {output_path}")

