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
import math

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760

TEXT_WHITE = (255, 255, 255, 255)
TEXT_SOFT = (230, 230, 230, 255)
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


def get_accent_colors(image):
    img_small = image.resize((150, 150), Image.LANCZOS)
    pixels = list(img_small.getdata())
    
    color_counts = {}
    for pixel in pixels:
        if pixel[0] + pixel[1] + pixel[2] > 100:
            color_counts[pixel] = color_counts.get(pixel, 0) + 1
    
    if not color_counts:
        return [(100, 200, 255, 255), (255, 100, 200, 255)]
    
    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
    
    def enhance_color(rgb):
        h, s, v = rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        s = min(1.0, s * 2.5)
        v = max(0.65, min(0.95, v * 1.5))
        r, g, b = hsv_to_rgb(h, s, v)
        return (int(r*255), int(g*255), int(b*255), 255)
    
    color1 = enhance_color(sorted_colors[0][0][:3])
    color2 = enhance_color(sorted_colors[min(len(sorted_colors)-1, 30)][0][:3])
    
    return [color1, color2]


def create_gradient_background(size, colors):
    gradient = Image.new('RGBA', size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(gradient)
    
    for y in range(size[1]):
        progress = y / size[1]
        
        r = int(colors[0][0] * (1-progress) + colors[1][0] * progress)
        g = int(colors[0][1] * (1-progress) + colors[1][1] * progress)
        b = int(colors[0][2] * (1-progress) + colors[1][2] * progress)
        
        draw.line([(0, y), (size[0], y)], fill=(r, g, b, 255))
    
    dark_overlay = Image.new('RGBA', size, (0, 0, 0, 150))
    gradient = Image.alpha_composite(gradient, dark_overlay)
    
    return gradient


def create_radial_glow(size, center, color, max_radius):
    glow = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    
    steps = 40
    for i in range(steps):
        progress = i / steps
        radius = int(max_radius * progress)
        alpha = int(150 * (1 - progress))
        
        glow_color = (*color[:3], alpha)
        draw.ellipse(
            [center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius],
            fill=glow_color
        )
    
    return glow.filter(ImageFilter.GaussianBlur(30))


def create_vinyl_disc(base_img, size, accent_color):
    disc = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    disc_bg = Image.new('RGBA', (size, size), (25, 25, 30, 255))
    disc_draw = ImageDraw.Draw(disc_bg)
    
    for i in range(15):
        groove_radius = size//2 - 40 - (i * 15)
        if groove_radius > 0:
            alpha = 30 + (i * 5)
            disc_draw.ellipse(
                [size//2-groove_radius, size//2-groove_radius, 
                 size//2+groove_radius, size//2+groove_radius],
                outline=(255, 255, 255, alpha),
                width=2
            )
    
    center_size = int(size * 0.4)
    mask = Image.new('L', (center_size, center_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, center_size, center_size], fill=255)
    
    center_art = base_img.resize((center_size, center_size), Image.LANCZOS)
    center_art.putalpha(mask)
    
    disc.paste(disc_bg, (0, 0))
    disc.paste(center_art, ((size-center_size)//2, (size-center_size)//2), center_art)
    
    outer_mask = Image.new('L', (size, size), 0)
    outer_draw = ImageDraw.Draw(outer_mask)
    outer_draw.ellipse([0, 0, size, size], fill=255)
    disc.putalpha(outer_mask)
    
    glow_size = size + 60
    glow_frame = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
    
    for i in range(5):
        offset = i * 12
        alpha = 180 - (i * 35)
        layer = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.ellipse(
            [offset, offset, glow_size-offset, glow_size-offset],
            outline=(*accent_color[:3], alpha),
            width=8
        )
        layer = layer.filter(ImageFilter.GaussianBlur(10))
        glow_frame = Image.alpha_composite(glow_frame, layer)
    
    glow_frame.paste(disc, (30, 30), disc)
    
    return glow_frame


def create_music_waves(size, color):
    waves = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(waves)
    
    wave_count = 3
    for wave_idx in range(wave_count):
        points = []
        amplitude = 30 + (wave_idx * 15)
        frequency = 0.02 + (wave_idx * 0.01)
        y_base = size[1] - 100 - (wave_idx * 40)
        
        for x in range(size[0] + 50):
            y = y_base + math.sin(x * frequency) * amplitude
            points.append((x, int(y)))
        
        alpha = 60 - (wave_idx * 15)
        wave_color = (*color[:3], alpha)
        
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=wave_color, width=3)
    
    return waves.filter(ImageFilter.GaussianBlur(5))


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
        accent_colors = get_accent_colors(base_img)
        
        gradient_bg = create_gradient_background((CANVAS_W, CANVAS_H), accent_colors)
        
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        canvas = Image.alpha_composite(canvas, gradient_bg)
        
        glow_layer = create_radial_glow(
            (CANVAS_W, CANVAS_H), 
            (350, CANVAS_H//2), 
            accent_colors[0], 
            500
        )
        canvas = Image.alpha_composite(canvas, glow_layer)
        
        waves = create_music_waves((CANVAS_W, CANVAS_H), accent_colors[1])
        canvas = Image.alpha_composite(canvas, waves)
        
        disc_size = 420
        vinyl = create_vinyl_disc(base_img, disc_size, accent_colors[0])
        disc_x = 80
        disc_y = (CANVAS_H - vinyl.height) // 2
        canvas.paste(vinyl, (disc_x, disc_y), vinyl)
        
        draw = ImageDraw.Draw(canvas)
        
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
        brand_text = "ShrutiMusic"
        shadow_offset = 4
        
        draw.text((40+shadow_offset, 30+shadow_offset), brand_text, fill=(0, 0, 0, 200), font=brand_font)
        draw.text((40, 30), brand_text, fill=TEXT_WHITE, font=brand_font)
        
        info_x = disc_x + vinyl.width + 40
        max_text_w = CANVAS_W - info_x - 50
        
        now_font = ImageFont.truetype(FONT_BOLD_PATH, 48)
        now_text = "♪ NOW PLAYING"
        now_y = 100
        
        draw.text((info_x+3, now_y+3), now_text, fill=TEXT_SHADOW, font=now_font)
        draw.text((info_x, now_y), now_text, fill=accent_colors[0], font=now_font)
        
        separator_y = now_y + 65
        draw.rectangle(
            [info_x, separator_y, info_x + max_text_w - 100, separator_y + 3],
            fill=(*accent_colors[0][:3], 150)
        )
        
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 40)
        title_lines = wrap_text(draw, title, title_font, max_text_w)
        title_text = "\n".join(title_lines)
        title_y = separator_y + 30
        
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
        
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        meta_y = title_y + 150
        line_gap = 48
        
        duration_label = duration
        if duration and ":" in duration and "Min" not in duration and "min" not in duration:
            duration_label = f"{duration} Mins"
        
        meta_items = [
            ("👁", views),
            ("⏱", duration_label),
            ("📺", channel)
        ]
        
        for idx, (icon, value) in enumerate(meta_items):
            y_pos = meta_y + (idx * line_gap)
            meta_text = f"{icon}  {value}"
            
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
