# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com
#
# ATLEAST GIVE CREDITS IF YOU STEALING :
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import os
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from colorsys import rgb_to_hsv, hsv_to_rgb

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760
BG_BLUR = 25
BG_DARKNESS = 0.35

TEXT_WHITE = (255, 255, 255, 255)
TEXT_SOFT = (240, 240, 240, 255)
TEXT_SHADOW = (0, 0, 0, 200)

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"


def change_image_size(max_w, max_h, image):
    ratio = min(max_w / image.size[0], max_h / image.size[1])
    return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines[:2]


def get_vibrant_edge_color(image):
    img_small = image.resize((80, 80), Image.LANCZOS)
    pixels = list(img_small.getdata())
    
    edge_pixels = []
    size = 80
    thickness = 15
    
    for i in range(size):
        for j in range(thickness):
            edge_pixels.append(pixels[i + j * size])
            edge_pixels.append(pixels[i * size + j])
            edge_pixels.append(pixels[i * size + (size - 1 - j)])
            edge_pixels.append(pixels[(size - 1 - j) * size + i])
    
    r_avg = sum(p[0] for p in edge_pixels) // len(edge_pixels)
    g_avg = sum(p[1] for p in edge_pixels) // len(edge_pixels)
    b_avg = sum(p[2] for p in edge_pixels) // len(edge_pixels)
    
    h, s, v = rgb_to_hsv(r_avg/255, g_avg/255, b_avg/255)
    s = min(1.0, s * 2.2)
    v = max(0.7, min(1.0, v * 1.6))
    
    r, g, b = hsv_to_rgb(h, s, v)
    return (int(r*255), int(g*255), int(b*255), 255)


def create_edge_glow(size, glow_color):
    glow = Image.new('RGBA', size, (0, 0, 0, 0))
    
    glow_layers = [
        (10, 220, 30),
        (25, 180, 25),
        (40, 140, 20),
        (60, 100, 18),
        (80, 70, 15),
        (100, 40, 12),
        (120, 20, 10)
    ]
    
    for offset, alpha, width in glow_layers:
        layer = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        color = (*glow_color[:3], alpha)
        draw.rectangle(
            [offset, offset, size[0]-offset, size[1]-offset],
            outline=color,
            width=width
        )
        layer = layer.filter(ImageFilter.GaussianBlur(20))
        glow = Image.alpha_composite(glow, layer)
    
    return glow


def create_artwork_with_frame(base_img, size, glow_color):
    art = base_img.resize((size, size), Image.LANCZOS)
    
    corner_radius = 40
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=corner_radius, fill=255)
    
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(art, (0, 0))
    output.putalpha(mask)
    
    frame_size = size + 40
    frame = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
    
    glow_layers = [
        (35, 200, 8),
        (28, 160, 6),
        (20, 120, 5),
        (12, 80, 4),
        (5, 50, 3)
    ]
    
    for offset, alpha, width in glow_layers:
        layer = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        color = (*glow_color[:3], alpha)
        x = offset
        y = offset
        w = frame_size - offset * 2
        h = frame_size - offset * 2
        draw.rounded_rectangle([x, y, x+w, y+h], radius=corner_radius+10, outline=color, width=width)
        layer = layer.filter(ImageFilter.GaussianBlur(8))
        frame = Image.alpha_composite(frame, layer)
    
    frame.paste(output, (20, 20), output)
    
    return frame


async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
        except:
            pass

        if thumb_path and thumb_path.exists():
            base_img = Image.open(thumb_path).convert("RGBA")
        else:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    except Exception as e:
        print(f"[gen_thumb Error - Using Default] {e}")
        try:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
            title = "ShrutiMusic"
            duration = "Unknown"
            views = "Unknown Views"
            channel = "ShrutiBots"
        except:
            traceback.print_exc()
            return None

    try:
        bg = change_image_size(CANVAS_W, CANVAS_H, base_img).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(BG_BLUR))
        bg = ImageEnhance.Brightness(bg).enhance(BG_DARKNESS)
        
        dark_overlay = Image.new('RGBA', bg.size, (0, 0, 0, 120))
        bg = Image.alpha_composite(bg, dark_overlay)
        
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (15, 15, 20, 255))
        canvas.paste(bg, (0, 0))
        
        edge_color = get_vibrant_edge_color(base_img)
        glow_layer = create_edge_glow((CANVAS_W, CANVAS_H), edge_color)
        canvas = Image.alpha_composite(canvas, glow_layer)
        
        draw = ImageDraw.Draw(canvas)

        art_size = 480
        artwork_frame = create_artwork_with_frame(base_img, art_size, edge_color)
        art_x = 70
        art_y = (CANVAS_H - artwork_frame.height) // 2
        canvas.paste(artwork_frame, (art_x, art_y), artwork_frame)

        tl_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        shadow_offset = 3
        draw.text((35+shadow_offset, 25+shadow_offset), "ShrutiMusic", fill=TEXT_SHADOW, font=tl_font)
        draw.text((35, 25), "ShrutiMusic", fill=TEXT_WHITE, font=tl_font)

        info_x = art_x + artwork_frame.width + 50
        max_text_w = CANVAS_W - info_x - 60

        np_font = ImageFont.truetype(FONT_BOLD_PATH, 75)
        np_text = "NOW PLAYING"
        np_x = info_x
        np_y = 120
        
        shadow_offset = 4
        draw.text((np_x+shadow_offset, np_y+shadow_offset), np_text, fill=TEXT_SHADOW, font=np_font)
        draw.text((np_x, np_y), np_text, fill=TEXT_WHITE, font=np_font)

        title_font_size = 38
        title_font = ImageFont.truetype(FONT_BOLD_PATH, title_font_size)
        title_lines = wrap_text(draw, title, title_font, max_text_w)
        title_text = "\n".join(title_lines)
        title_y = np_y + 100
        
        draw.multiline_text(
            (info_x+3, title_y+3), 
            title_text, 
            fill=TEXT_SHADOW, 
            font=title_font, 
            spacing=10
        )
        draw.multiline_text(
            (info_x, title_y), 
            title_text, 
            fill=TEXT_WHITE, 
            font=title_font, 
            spacing=10
        )

        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 32)
        meta_start_y = title_y + 140
        line_gap = 52
        
        duration_label = duration
        if duration and ":" in duration and "Min" not in duration and "min" not in duration:
            duration_label = f"{duration} Mins"

        meta_items = [
            f"Views : {views}",
            f"Duration : {duration_label}",
            f"Channel : {channel}"
        ]
        
        for idx, meta_text in enumerate(meta_items):
            y_pos = meta_start_y + (idx * line_gap)
            draw.text((info_x+2, y_pos+2), meta_text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x, y_pos), meta_text, fill=TEXT_SOFT, font=meta_font)

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95, optimize=True)

        if thumb_path and thumb_path.exists():
            try:
                os.remove(thumb_path)
            except:
                pass

        return str(out)

    except Exception as e:
        print(f"[gen_thumb Processing Error] {e}")
        traceback.print_exc()
        return None
