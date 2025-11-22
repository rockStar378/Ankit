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

TEXT_WHITE = (255, 255, 255, 255)
TEXT_SOFT = (220, 220, 220, 255)
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


def extract_vibrant_color(image):
    img_small = image.resize((100, 100), Image.LANCZOS)
    pixels = list(img_small.getdata())
    
    edge_pixels = []
    for i in range(100):
        edge_pixels.extend([
            pixels[i],
            pixels[i * 100],
            pixels[(i + 1) * 100 - 1],
            pixels[9900 + i]
        ])
    
    r_sum = sum(p[0] for p in edge_pixels)
    g_sum = sum(p[1] for p in edge_pixels)
    b_sum = sum(p[2] for p in edge_pixels)
    count = len(edge_pixels)
    
    r_avg, g_avg, b_avg = r_sum // count, g_sum // count, b_sum // count
    
    h, s, v = rgb_to_hsv(r_avg/255, g_avg/255, b_avg/255)
    s = min(1.0, s * 2.0)
    v = max(0.6, min(0.9, v * 1.4))
    
    r, g, b = hsv_to_rgb(h, s, v)
    return (int(r*255), int(g*255), int(b*255), 255)


def create_glowing_border(size, glow_color, border_width=8, glow_spread=80):
    border = Image.new('RGBA', size, (0, 0, 0, 0))
    
    glow_steps = [
        (glow_spread, 15, 200),
        (glow_spread * 0.75, 12, 160),
        (glow_spread * 0.5, 10, 120),
        (glow_spread * 0.35, 8, 80),
        (glow_spread * 0.2, 6, 50),
        (glow_spread * 0.1, 4, 30)
    ]
    
    for spread, width, alpha in glow_steps:
        layer = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        for offset in range(int(spread)):
            current_alpha = int(alpha * (1 - offset/spread))
            color = (*glow_color[:3], current_alpha)
            
            draw.rectangle(
                [offset, offset, size[0]-offset-1, size[1]-offset-1],
                outline=color,
                width=1
            )
        
        layer = layer.filter(ImageFilter.GaussianBlur(spread/4))
        border = Image.alpha_composite(border, layer)
    
    draw = ImageDraw.Draw(border)
    draw.rectangle(
        [glow_spread-border_width, glow_spread-border_width, 
         size[0]-glow_spread+border_width, size[1]-glow_spread+border_width],
        outline=(*glow_color[:3], 255),
        width=border_width
    )
    
    return border


def create_thumbnail_frame(base_img, size, glow_color):
    corner_radius = 25
    
    mask = Image.new('L', size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size[0], size[1]], radius=corner_radius, fill=255)
    
    thumb = base_img.resize(size, Image.LANCZOS)
    thumb.putalpha(mask)
    
    frame_glow = Image.new('RGBA', (size[0]+60, size[1]+60), (0, 0, 0, 0))
    
    for i in range(6):
        offset = 5 + (i * 8)
        alpha = 200 - (i * 30)
        blur_amount = 8 + (i * 2)
        
        layer = Image.new('RGBA', (size[0]+60, size[1]+60), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        
        layer_draw.rounded_rectangle(
            [offset, offset, size[0]+60-offset, size[1]+60-offset],
            radius=corner_radius+15,
            outline=(*glow_color[:3], alpha),
            width=6
        )
        
        layer = layer.filter(ImageFilter.GaussianBlur(blur_amount))
        frame_glow = Image.alpha_composite(frame_glow, layer)
    
    frame_glow.paste(thumb, (30, 30), thumb)
    
    return frame_glow


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
        bg = bg.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Brightness(bg).enhance(0.25)
        
        dark_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (10, 10, 15, 200))
        bg = Image.alpha_composite(bg, dark_layer)
        
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (8, 8, 12, 255))
        canvas.paste(bg, (0, 0))
        
        accent_color = extract_vibrant_color(base_img)
        
        border_glow = create_glowing_border((CANVAS_W, CANVAS_H), accent_color, border_width=6, glow_spread=70)
        canvas = Image.alpha_composite(canvas, border_glow)
        
        thumb_size = (440, 440)
        thumbnail_frame = create_thumbnail_frame(base_img, thumb_size, accent_color)
        
        thumb_x = 90
        thumb_y = (CANVAS_H - thumbnail_frame.height) // 2
        canvas.paste(thumbnail_frame, (thumb_x, thumb_y), thumbnail_frame)
        
        draw = ImageDraw.Draw(canvas)
        
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 46)
        brand_x = 45
        brand_y = 35
        
        draw.text((brand_x+3, brand_y+3), "ShrutiMusic", fill=TEXT_SHADOW, font=brand_font)
        draw.text((brand_x, brand_y), "ShrutiMusic", fill=TEXT_WHITE, font=brand_font)
        
        info_x = thumb_x + thumbnail_frame.width + 50
        max_text_w = CANVAS_W - info_x - 50
        
        now_font = ImageFont.truetype(FONT_BOLD_PATH, 70)
        now_text = "NOW PLAYING"
        now_y = 110
        
        draw.text((info_x+4, now_y+4), now_text, fill=TEXT_SHADOW, font=now_font)
        draw.text((info_x, now_y), now_text, fill=TEXT_WHITE, font=now_font)
        
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 40)
        title_lines = wrap_text(draw, title, title_font, max_text_w)
        title_text = "\n".join(title_lines)
        title_y = now_y + 100
        
        draw.multiline_text(
            (info_x+3, title_y+3),
            title_text,
            fill=TEXT_SHADOW,
            font=title_font,
            spacing=12
        )
        draw.multiline_text(
            (info_x, title_y),
            title_text,
            fill=TEXT_WHITE,
            font=title_font,
            spacing=12
        )
        
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 34)
        meta_y = title_y + 160
        line_gap = 55
        
        duration_label = duration
        if duration and ":" in duration and "Min" not in duration and "min" not in duration:
            duration_label = f"{duration} Mins"
        
        meta_items = [
            f"Views : {views}",
            f"Duration : {duration_label}",
            f"Channel : {channel}"
        ]
        
        for idx, meta_text in enumerate(meta_items):
            y_pos = meta_y + (idx * line_gap)
            
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
