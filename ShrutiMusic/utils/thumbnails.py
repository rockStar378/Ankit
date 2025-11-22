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
BG_BLUR = 18
BG_BRIGHTNESS = 0.85

TEXT_WHITE = (255, 255, 255, 255)
TEXT_SOFT = (240, 240, 240, 255)
TEXT_SHADOW = (0, 0, 0, 180)

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
    img_small = image.resize((100, 100), Image.LANCZOS)
    pixels = list(img_small.getdata())
    
    edge_pixels = []
    size = 100
    for i in range(size):
        edge_pixels.append(pixels[i])
        edge_pixels.append(pixels[i * size])
        edge_pixels.append(pixels[(i + 1) * size - 1])
        edge_pixels.append(pixels[size * (size - 1) + i])
    
    r_avg = sum(p[0] for p in edge_pixels) // len(edge_pixels)
    g_avg = sum(p[1] for p in edge_pixels) // len(edge_pixels)
    b_avg = sum(p[2] for p in edge_pixels) // len(edge_pixels)
    
    h, s, v = rgb_to_hsv(r_avg/255, g_avg/255, b_avg/255)
    s = min(1.0, s * 1.8)
    v = max(0.6, min(0.95, v * 1.4))
    
    r, g, b = hsv_to_rgb(h, s, v)
    return (int(r*255), int(g*255), int(b*255), 255)


def create_premium_glow(size, glow_color, intensity=1.0):
    glow = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    
    layers = [
        (0, int(180 * intensity)),
        (15, int(140 * intensity)),
        (30, int(100 * intensity)),
        (45, int(70 * intensity)),
        (60, int(40 * intensity)),
        (75, int(20 * intensity))
    ]
    
    for offset, alpha in layers:
        color = (*glow_color[:3], alpha)
        draw.rectangle(
            [offset, offset, size[0]-offset, size[1]-offset],
            outline=color,
            width=int(15 + (offset/10))
        )
    
    glow = glow.filter(ImageFilter.GaussianBlur(25))
    return glow


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
        bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHTNESS)
        
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        gradient_height = 150
        for i in range(gradient_height):
            alpha = int((i / gradient_height) * 100)
            overlay_draw.rectangle(
                [(0, CANVAS_H - gradient_height + i), (CANVAS_W, CANVAS_H - gradient_height + i + 1)],
                fill=(0, 0, 0, alpha)
            )
        
        bg = Image.alpha_composite(bg, overlay)
        
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        canvas.paste(bg, (0, 0))
        
        edge_color = get_vibrant_edge_color(base_img)
        glow_layer = create_premium_glow((CANVAS_W, CANVAS_H), edge_color, intensity=1.2)
        canvas = Image.alpha_composite(canvas, glow_layer)
        
        draw = ImageDraw.Draw(canvas)

        thumb_size = 500
        circle_x = 80
        circle_y = (CANVAS_H - thumb_size) // 2

        circular_mask = Image.new("L", (thumb_size, thumb_size), 0)
        mdraw = ImageDraw.Draw(circular_mask)
        mdraw.ellipse((0, 0, thumb_size, thumb_size), fill=255)

        art = base_img.resize((thumb_size, thumb_size), Image.LANCZOS)
        art.putalpha(circular_mask)

        ring_width = 8
        ring_size = thumb_size + ring_width * 2
        ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(ring_img)
        
        ring_glow_color = edge_color
        for i in range(3):
            offset = i * 6
            alpha = 180 - (i * 40)
            rdraw.ellipse(
                [offset, offset, ring_size - offset, ring_size - offset],
                outline=(*ring_glow_color[:3], alpha),
                width=ring_width + (i * 2)
            )
        
        ring_img = ring_img.filter(ImageFilter.GaussianBlur(4))
        
        canvas.paste(ring_img, (circle_x - ring_width, circle_y - ring_width), ring_img)
        canvas.paste(art, (circle_x, circle_y), art)

        tl_font = ImageFont.truetype(FONT_BOLD_PATH, 40)
        tl_shadow_offset = 3
        draw.text((35+tl_shadow_offset, 25+tl_shadow_offset), "ShrutiMusic", fill=(0, 0, 0, 200), font=tl_font)
        draw.text((35, 25), "ShrutiMusic", fill=TEXT_WHITE, font=tl_font)

        info_x = circle_x + thumb_size + 70
        max_text_w = CANVAS_W - info_x - 60

        np_font = ImageFont.truetype(FONT_BOLD_PATH, 75)
        np_text = "NOW PLAYING"
        np_bbox = draw.textbbox((0, 0), np_text, font=np_font)
        np_w = np_bbox[2] - np_bbox[0]
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
