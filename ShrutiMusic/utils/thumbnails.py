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

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760
BG_BLUR = 16
BG_BRIGHTNESS = 1  

RING_COLOR = (98, 193, 169, 255)
TEXT_WHITE = (245, 245, 245, 255)
TEXT_SOFT = (230, 230, 230, 255)
TEXT_SHADOW = (0, 0, 0, 140)

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"

FONT_REGULAR = ImageFont.truetype(FONT_REGULAR_PATH, 30)
FONT_BOLD = ImageFont.truetype(FONT_BOLD_PATH, 30)


def change_image_size(max_w, max_h, image):
    ratio = min(max_w / image.size[0], max_h / image.size[1])
    return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)


def wrap_two_lines(draw, text, font, max_width):
    words = text.split()
    line1, line2 = "", ""
    for w in words:
        test = (line1 + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            line1 = test
        else:
            break
    remaining = text[len(line1):].strip()
    if remaining:
        for w in remaining.split():
            test = (line2 + " " + w).strip()
            if draw.textlength(test, font=font) <= max_width:
                line2 = test
            else:
                break
    return (line1 + ("\n" + line2 if line2 else "")).strip()


def fit_title_two_lines(draw, text, max_width, font_path, start_size=58, min_size=30):
    size = start_size
    while size >= min_size:
        try:
            f = ImageFont.truetype(font_path, size)
        except:
            size -= 1
            continue
        wrapped = wrap_two_lines(draw, text, f, max_width)
        lines = wrapped.split("\n")
        if len(lines) <= 2 and all(draw.textlength(l, font=f) <= max_width for l in lines):
            return f, wrapped
        size -= 1
    f = ImageFont.truetype(font_path, min_size)
    return f, wrap_two_lines(draw, text, f, max_width)


def get_dominant_edge_color(image, sample_size=50):
    img_small = image.resize((sample_size, sample_size), Image.LANCZOS)
    pixels = list(img_small.getdata())
    
    edge_pixels = []
    for i in range(sample_size):
        edge_pixels.append(pixels[i])
        edge_pixels.append(pixels[i * sample_size])
        edge_pixels.append(pixels[(i + 1) * sample_size - 1])
        edge_pixels.append(pixels[sample_size * (sample_size - 1) + i])
    
    r_avg = sum(p[0] for p in edge_pixels) // len(edge_pixels)
    g_avg = sum(p[1] for p in edge_pixels) // len(edge_pixels)
    b_avg = sum(p[2] for p in edge_pixels) // len(edge_pixels)
    
    brightness = (r_avg + g_avg + b_avg) / 3
    saturation_boost = 1.5 if brightness < 100 else 1.3
    
    r_boosted = min(255, int(r_avg * saturation_boost))
    g_boosted = min(255, int(g_avg * saturation_boost))
    b_boosted = min(255, int(b_avg * saturation_boost))
    
    return (r_boosted, g_boosted, b_boosted, 255)


def add_dynamic_edge_glow(canvas, glow_color, corner_radius=40):
    width, height = canvas.size
    
    glow_layers = []
    glow_intensities = [
        (45, 120),
        (35, 90),
        (25, 60),
        (15, 35),
        (8, 20)
    ]
    
    for offset, alpha in glow_intensities:
        glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        
        current_color = (*glow_color[:3], alpha)
        
        x0, y0 = offset, offset
        x1, y1 = width - offset, height - offset
        
        glow_draw.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=corner_radius,
            outline=current_color,
            width=8
        )
        
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(12))
        glow_layers.append(glow_layer)
    
    for glow_layer in reversed(glow_layers):
        canvas = Image.alpha_composite(canvas, glow_layer)
    
    inner_glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    inner_draw = ImageDraw.Draw(inner_glow)
    
    for i, (inset, alpha) in enumerate([(5, 40), (12, 25), (20, 15)]):
        inner_color = (*glow_color[:3], alpha)
        inner_draw.rounded_rectangle(
            [inset, inset, width - inset, height - inset],
            radius=corner_radius - (i * 3),
            outline=inner_color,
            width=6
        )
    
    inner_glow = inner_glow.filter(ImageFilter.GaussianBlur(8))
    canvas = Image.alpha_composite(canvas, inner_glow)
    
    return canvas


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

        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        canvas.paste(bg, (0, 0))
        
        edge_color = get_dominant_edge_color(base_img)
        canvas = add_dynamic_edge_glow(canvas, edge_color, corner_radius=45)
        
        draw = ImageDraw.Draw(canvas)

        thumb_size = 470
        ring_width = 20
        circle_x = 92
        circle_y = (CANVAS_H - thumb_size) // 2

        circular_mask = Image.new("L", (thumb_size, thumb_size), 0)
        mdraw = ImageDraw.Draw(circular_mask)
        mdraw.ellipse((0, 0, thumb_size, thumb_size), fill=255)

        art = base_img.resize((thumb_size, thumb_size))
        art.putalpha(circular_mask)

        ring_size = thumb_size + ring_width * 2
        ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(ring_img)
        ring_bbox = (ring_width//2, ring_width//2, ring_size - ring_width//2, ring_size - ring_width//2)
        rdraw.ellipse(ring_bbox, outline=RING_COLOR, width=ring_width)

        canvas.paste(ring_img, (circle_x - ring_width, circle_y - ring_width), ring_img)
        canvas.paste(art, (circle_x, circle_y), art)

        tl_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
        draw.text((28+1, 18+1), "ShrutiMusic", fill=TEXT_SHADOW, font=tl_font)
        draw.text((28, 18), "ShrutiMusic", fill=TEXT_WHITE, font=tl_font)

        info_x = circle_x + thumb_size + 60
        max_text_w = CANVAS_W - info_x - 48

        np_font = ImageFont.truetype(FONT_BOLD_PATH, 60)
        np_text = "NOW PLAYING"
        np_w = draw.textlength(np_text, font=np_font)
        np_x = info_x + (max_text_w - np_w) // 2 - 95
        np_y = circle_y + 30  
        draw.text((np_x+2, np_y+2), np_text, fill=TEXT_SHADOW, font=np_font)
        draw.text((np_x, np_y), np_text, fill=TEXT_WHITE, font=np_font)

        title_font, title_wrapped = fit_title_two_lines(draw, title, max_text_w, FONT_BOLD_PATH, start_size=30, min_size=30)
        title_y = np_y + 110   
        draw.multiline_text((info_x+2, title_y+2), title_wrapped, fill=TEXT_SHADOW, font=title_font, spacing=8)
        draw.multiline_text((info_x, title_y), title_wrapped, fill=TEXT_WHITE, font=title_font, spacing=8)

        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        line_gap = 46
        meta_start_y = title_y + 130  
        duration_label = duration
        if duration and ":" in duration and "Min" not in duration and "min" not in duration:
            duration_label = f"{duration} Mins"

        def draw_meta(y, text):
            draw.text((info_x+1, y+1), text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x, y), text, fill=TEXT_SOFT, font=meta_font)

        draw_meta(meta_start_y + 0 * line_gap, f"Views : {views}")
        draw_meta(meta_start_y + 1 * line_gap, f"Duration : {duration_label}")
        draw_meta(meta_start_y + 2 * line_gap, f"Channel : {channel}")

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out)

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
