import os
import json
import time
import asyncio
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from google import genai
from moviepy.editor import VideoClip, AudioFileClip, concatenate_videoclips

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """
Придумай захватывающую, напряженную сюжетную историю-притчу от первого лица в духе криминальной драмы «Снегопад» (Snowfall) и персонажа Франклина Сейнта (Franklin Saint) для TikTok длительностью РОВНО 55-65 секунд (около 130-150 слов текста озвучки) на русском языке.
Темы на выбор (чередуй их): цена легких денег, предательство лучшего друга, холодный расчет против эмоций, проверка на верность, как власть меняет человека, правила выживания на улицах Лос-Анджелеса 1980-х.
История обязана иметь:
1) Мощный интригующий крючок в 1-й фразе.
2) Напряженный конфликт в середине.
3) Неожиданный поворот (твист) и глубокую, жесткую мораль в финале.
Тон речи: хладнокровный, умный, спокойный, без пафосных клише.

Главный герой во всех сценах строго один и тот же: молодой темнокожий парень 20 лет (внешность как Франклин Сейнт), короткая аккуратная стрижка афро, серьезный проницательный взгляд, черная расстегнутая куртка поверх кремовой рубашки с отложным воротником, тонкая золотая цепочка, темные брюки.
Атмосфера: 1980s South Central Los Angeles, закат или неоновая ночь, пальмы, классические американские седаны 80-х, уличные фонари.

Разбей историю ровно на 12 динамичных сцен (по 1-2 коротких предложения на сцену, примерно 11-13 слов в каждой).
Верни ответ СТРОГО в формате JSON без маркдауна:
{
  "title": "Интригующий заголовок истории с 3 хэштегами",
  "character_style": "1980s South Central Los Angeles 2D comic animation style like The Boondocks, bold black ink outlines, young 20yo Black man resembling Franklin Saint with short neat afro hair, wearing black zip jacket over unbuttoned cream collared shirt, thin gold chain, warm sunset or moody night lighting, cinematic framing, vertical 9:16, no text",
  "scenes": [
    {"text": "Текст 1 сцены (хук)", "image_prompt": "Close-up shot in English of the main character..."},
    {"text": "Текст 2 сцены", "image_prompt": "Medium shot in English..."},
    {"text": "Текст 3 сцены", "image_prompt": "Wide street shot in English..."},
    {"text": "Текст 4 сцены", "image_prompt": "Scene 4 in English..."},
    {"text": "Текст 5 сцены", "image_prompt": "Scene 5 in English..."},
    {"text": "Текст 6 сцены", "image_prompt": "Scene 6 in English..."},
    {"text": "Текст 7 сцены", "image_prompt": "Scene 7 in English..."},
    {"text": "Текст 8 сцены", "image_prompt": "Scene 8 in English..."},
    {"text": "Текст 9 сцены", "image_prompt": "Scene 9 in English..."},
    {"text": "Текст 10 сцены (поворот)", "image_prompt": "Dramatic close-up in English..."},
    {"text": "Текст 11 сцены", "image_prompt": "Scene 11 in English..."},
    {"text": "Текст 12 сцены (финальная мораль)", "image_prompt": "Back view of the main character looking at sunset Los Angeles skyline with palm trees..."}
  ]
}
"""

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
)

raw_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
data = json.loads(raw_text)
print("Заголовок:", data["title"])

async def make_audio(text, filename):
    # Глубокий, спокойный и уверенный голос рассказчика
    communicate = edge_tts.Communicate(text, "ru-RU-DmitryNeural", rate="+2%", pitch="-8Hz")
    await communicate.save(filename)

def add_word_subtitle(pil_img, word):
    draw = ImageDraw.Draw(pil_img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 76)
    
    clean_word = word.strip(".,!?\"'«»—-").upper()
    if not clean_word:
        return pil_img

    bbox = draw.textbbox((0, 0), clean_word, font=font)
    w = bbox - bbox
    x_text = (1080 - w) / 2
    y_text = 1480
    
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            draw.text((x_text + dx, y_text + dy), clean_word, font=font, fill="black")
    draw.text((x_text, y_text), clean_word, font=font, fill="white")
    return pil_img

clips = []
style_suffix = data.get("character_style", "1980s 2D comic animation style, bold black ink outlines, vertical 9:16, no text")

for i, scene in enumerate(data["scenes"]):
    img_path = f"img_{i}.jpg"
    aud_path = f"aud_{i}.mp3"
    
    full_prompt = f"{scene['image_prompt']}, {style_suffix}"
    encoded_prompt = requests.utils.quote(full_prompt)
    base_url = "https://" + "image.pollinations.ai" + "/prompt/"
    img_url = f"{base_url}{encoded_prompt}?width=1080&height=1920&nologo=true&seed={300+i}"
    
    img_data = None
    for attempt in range(2):
        try:
            print(f"Сцена {i+1}/12: рисуем кадр (попытка {attempt+1})...")
            res = requests.get(img_url, timeout=45)
            if res.status_code == 200 and len(res.content) > 5000:
                img_data = res.content
                break
        except Exception:
            time.sleep(3)
            
    if not img_data:
        print(f"Сцена {i+1}: резервная картинка")
        fallback = "https://" + "picsum.photos" + f"/1080/1920?random={i+120}"
        img_data = requests.get(fallback, timeout=15).content

    with open(img_path, "wb") as f:
        f.write(img_data)
        
    asyncio.run(make_audio(scene["text"], aud_path))
    audio_clip = AudioFileClip(aud_path)
    duration = audio_clip.duration
    words = scene["text"].split()
    
    base_pil = Image.open(img_path).convert("RGB").resize((1080, 1920), Image.Resampling.LANCZOS)
    
    def make_frame(t, img=base_pil, dur=duration, w_list=words):
        zoom = 1.0 + 0.10 * (t / max(dur, 0.1))
        new_w, new_h = int(1080 * zoom), int(1920 * zoom)
        zoomed = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        left = (new_w - 1080) // 2
        top = (new_h - 1920) // 2
        cropped = zoomed.crop((left, top, left + 1080, top + 1920))
        
        if w_list:
            word_idx = min(int((t / max(dur, 0.1)) * len(w_list)), len(w_list) - 1)
            cropped = add_word_subtitle(cropped, w_list[word_idx])
        return np.array(cropped)

    video_clip = VideoClip(make_frame, duration=duration).set_audio(audio_clip)
    clips.append(video_clip)

final_video = concatenate_videoclips(clips, method="compose")
final_video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

with open("title.txt", "w", encoding="utf-8") as f:
    f.write(data["title"])

print("Минутный мультфильм про Франклина Сейнта готов!")

