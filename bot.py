import os
import json
import asyncio
import requests
import edge_tts
from google import genai
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# 1. Инициализация нейросети Google Gemini
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """
Придумай 1 короткий, шокирующий или малоизвестный факт для вирусного ролика в TikTok (длительностью 25-35 секунд) на русском языке.
Разбей рассказ ровно на 4 короткие сцены.
Верни ответ СТРОГО в формате JSON без маркдауна:
{
  "title": "Цепляющий заголовок для поста с 3 хэштегами",
  "scenes": [
    {"text": "Текст озвучки 1 сцены на русском", "image_prompt": "Detailed vertical cinematic image prompt in English, 9:16, photorealistic, no text"},
    {"text": "Текст озвучки 2 сцены на русском", "image_prompt": "Detailed vertical cinematic image prompt in English, 9:16, photorealistic, no text"},
    {"text": "Текст озвучки 3 сцены на русском", "image_prompt": "Detailed vertical cinematic image prompt in English, 9:16, photorealistic, no text"},
    {"text": "Текст озвучки 4 сцены на русском", "image_prompt": "Detailed vertical cinematic image prompt in English, 9:16, photorealistic, no text"}
  ]
}
"""

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
)

# Очистка ответа от лишних символов
raw_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
data = json.loads(raw_text)

print("Заголовок:", data["title"])

# 2. Функция для бесплатной озвучки текста
async def make_audio(text, filename):
    communicate = edge_tts.Communicate(text, "ru-RU-DmitryNeural", rate="+10%")
    await communicate.save(filename)

clips = []

# 3. Сборка каждой сцены (картинка + звук)
for i, scene in enumerate(data["scenes"]):
    img_path = f"img_{i}.jpg"
    aud_path = f"aud_{i}.mp3"
    
    # Скачиваем бесплатную картинку 9:16 через Pollinations.ai
    encoded_prompt = requests.utils.quote(scene["image_prompt"])
    img_url = f"https://pollinations.ai{encoded_prompt}?width=1080&height=1920&nologo=true"
    img_data = requests.get(img_url).content
    with open(img_path, "wb") as f:
        f.write(img_data)
        
    # Генерируем голос
    asyncio.run(make_audio(scene["text"], aud_path))
    
    # Соединяем картинку и аудио в видеофрагмент
    audio_clip = AudioFileClip(aud_path)
    image_clip = ImageClip(img_path).set_duration(audio_clip.duration).set_audio(audio_clip)
    clips.append(image_clip)

# 4. Склеиваем финальный ролик
final_video = concatenate_videoclips(clips, method="compose")
final_video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

# Сохраняем заголовок в текстовый файл
with open("title.txt", "w", encoding="utf-8") as f:
    f.write(data["title"])

print("Видео успешно собрано!")
