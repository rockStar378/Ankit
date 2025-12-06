# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Enhanced by Claude - Premium Multi-Style Thumbnail Generator
# Location: Supaul, Bihar

import os
import random
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

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"


class ThemeGenerator:
    """Different premium themes for thumbnails"""
    
    @staticmethod
    def get_random_theme():
        themes = [
            ThemeGenerator.neon_cyberpunk,
            ThemeGenerator.gradient_wave,
            ThemeGenerator.glassmorphism,
            ThemeGenerator.retro_synthwave,
            ThemeGenerator.minimalist_modern,
            ThemeGenerator.holographic,
            ThemeGenerator.dark_elegant,
            ThemeGenerator.vibrant_pop
        ]
        return random.choice(themes)
    
    @staticmethod
    def neon_cyberpunk(base_img):
        """Neon cyberpunk style with glowing edges"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)
        
        # Neon overlay
        overlay = Image.new('RGBA', bg.size, (138, 43, 226, 30))
        bg = Image.alpha_composite(bg, overlay)
        
        # Scan lines effect
        for i in range(0, CANVAS_H, 4):
            draw = ImageDraw.Draw(bg)
            draw.line([(0, i), (CANVAS_W, i)], fill=(0, 255, 255, 10), width=1)
        
        return bg, {
            'accent': (0, 255, 255, 255),
            'text': (255, 255, 255, 255),
            'glow': (138, 43, 226, 255),
            'style': 'neon'
        }
    
    @staticmethod
    def gradient_wave(base_img):
        """Smooth gradient wave design"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Brightness(bg).enhance(0.6)
        
        # Wave gradient overlay
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        for y in range(CANVAS_H):
            wave = int(math.sin(y / 80) * 30)
            progress = y / CANVAS_H
            r = int(255 * (1 - progress) + 138 * progress)
            g = int(50 * (1 - progress) + 43 * progress)
            b = int(150 * (1 - progress) + 226 * progress)
            alpha = int(80 * progress)
            
            draw.rectangle([(0, y), (CANVAS_W + wave, y + 1)], fill=(r, g, b, alpha))
        
        bg = Image.alpha_composite(bg, overlay)
        
        return bg, {
            'accent': (255, 100, 200, 255),
            'text': (255, 255, 255, 255),
            'glow': (138, 43, 226, 255),
            'style': 'wave'
        }
    
    @staticmethod
    def glassmorphism(base_img):
        """Modern glass effect"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(20))
        bg = ImageEnhance.Brightness(bg).enhance(0.7)
        
        # Frosted glass overlay
        overlay = Image.new('RGBA', bg.size, (255, 255, 255, 40))
        bg = Image.alpha_composite(bg, overlay)
        
        return bg, {
            'accent': (255, 255, 255, 200),
            'text': (255, 255, 255, 255),
            'glow': (200, 200, 255, 255),
            'style': 'glass'
        }
    
    @staticmethod
    def retro_synthwave(base_img):
        """80s synthwave vibes"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(22))
        bg = ImageEnhance.Brightness(bg).enhance(0.5)
        
        # Synthwave gradient
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        for y in range(CANVAS_H):
            progress = y / CANVAS_H
            if progress < 0.5:
                r, g, b = 255, int(0 + 100 * progress * 2), 200
            else:
                r, g, b = 255, 100, int(200 - 150 * (progress - 0.5) * 2)
            alpha = int(60 + 40 * progress)
            draw.rectangle([(0, y), (CANVAS_W, y + 1)], fill=(r, g, b, alpha))
        
        bg = Image.alpha_composite(bg, overlay)
        
        # Grid lines
        for i in range(0, CANVAS_H, 40):
            draw = ImageDraw.Draw(bg)
            draw.line([(0, i), (CANVAS_W, i)], fill=(255, 0, 255, 30), width=2)
        
        return bg, {
            'accent': (255, 0, 255, 255),
            'text': (255, 255, 255, 255),
            'glow': (255, 100, 255, 255),
            'style': 'synthwave'
        }
    
    @staticmethod
    def minimalist_modern(base_img):
        """Clean minimalist design"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(35))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)
        
        # Solid dark overlay
        overlay = Image.new('RGBA', bg.size, (20, 20, 30, 200))
        bg = Image.alpha_composite(bg, overlay)
        
        return bg, {
            'accent': (100, 200, 255, 255),
            'text': (255, 255, 255, 255),
            'glow': (100, 200, 255, 255),
            'style': 'minimal'
        }
    
    @staticmethod
    def holographic(base_img):
        """Holographic rainbow effect"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.55)
        
        # Rainbow gradient
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        for x in range(CANVAS_W):
            progress = x / CANVAS_W
            hue = progress
            r, g, b = hsv_to_rgb(hue, 0.8, 0.9)
            alpha = 60
            draw.rectangle([(x, 0), (x + 1, CANVAS_H)], fill=(int(r*255), int(g*255), int(b*255), alpha))
        
        bg = Image.alpha_composite(bg, overlay)
        
        return bg, {
            'accent': (255, 150, 255, 255),
            'text': (255, 255, 255, 255),
            'glow': (200, 150, 255, 255),
            'style': 'holographic'
        }
    
    @staticmethod
    def dark_elegant(base_img):
        """Dark premium look"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        bg = ImageEnhance.Brightness(bg).enhance(0.3)
        
        # Vignette effect
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        center_x, center_y = CANVAS_W // 2, CANVAS_H // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for y in range(CANVAS_H):
            for x in range(0, CANVAS_W, 5):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                alpha = int((dist / max_dist) * 150)
                draw.rectangle([(x, y), (x + 5, y + 1)], fill=(0, 0, 0, alpha))
        
        bg = Image.alpha_composite(bg, overlay)
        
        return bg, {
            'accent': (255, 215, 0, 255),
            'text': (255, 255, 255, 255),
            'glow': (255, 215, 0, 255),
            'style': 'elegant'
        }
    
    @staticmethod
    def vibrant_pop(base_img):
        """Vibrant colorful pop art"""
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")
        bg = ImageEnhance.Color(bg).enhance(1.8)
        bg = bg.filter(ImageFilter.GaussianBlur(20))
        bg = ImageEnhance.Brightness(bg).enhance(0.65)
        
        # Color blocks
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        colors = [(255, 0, 100, 30), (0, 255, 200, 30), (255, 200, 0, 30)]
        for i, color in enumerate(colors):
            y_start = int(i * (CANVAS_H / 3))
            draw.rectangle([(0, y_start), (CANVAS_W, y_start + CANVAS_H // 3)], fill=color)
        
        bg = Image.alpha_composite(bg, overlay)
        
        return bg, {
            'accent': (255, 50, 150, 255),
            'text': (255, 255, 255, 255),
            'glow': (255, 100, 200, 255),
            'style': 'pop'
        }


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


def create_dynamic_glow(size, color, style):
    """Different glow effects based on style"""
    glow = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    
    if style in ['neon', 'synthwave']:
        # Sharp neon glow
        for i in range(0, 100, 10):
            alpha = int(200 - i * 2)
            draw.rectangle([i, i, size[0]-i, size[1]-i], 
                         outline=(*color[:3], alpha), width=3)
    elif style == 'glass':
        # Soft diffused glow
        for i in range(0, 80, 8):
            alpha = int(120 - i * 1.5)
            draw.rectangle([i, i, size[0]-i, size[1]-i], 
                         outline=(255, 255, 255, alpha), width=2)
    else:
        # Standard glow
        for i in range(0, 90, 12):
            alpha = int(180 - i * 2)
            draw.rectangle([i, i, size[0]-i, size[1]-i], 
                         outline=(*color[:3], alpha), width=4)
    
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    return glow


def create_artwork_shape(art, theme_style):
    """Different artwork shapes based on theme"""
    thumb_size = 480
    
    if theme_style in ['minimal', 'glass']:
        # Rounded square
        mask = Image.new("L", (thumb_size, thumb_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, thumb_size, thumb_size], radius=50, fill=255)
        art = art.resize((thumb_size, thumb_size), Image.LANCZOS)
        art.putalpha(mask)
        return art, thumb_size
    
    elif theme_style in ['neon', 'synthwave', 'holographic']:
        # Hexagon
        mask = Image.new("L", (thumb_size, thumb_size), 0)
        draw = ImageDraw.Draw(mask)
        center = thumb_size // 2
        radius = thumb_size // 2 - 10
        points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            x = center + radius * math.cos(angle)
            y = center + radius * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=255)
        art = art.resize((thumb_size, thumb_size), Image.LANCZOS)
        art.putalpha(mask)
        return art, thumb_size
    
    else:
        # Circle (default)
        mask = Image.new("L", (thumb_size, thumb_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([0, 0, thumb_size, thumb_size], fill=255)
        art = art.resize((thumb_size, thumb_size), Image.LANCZOS)
        art.putalpha(mask)
        return art, thumb_size


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
        print(f"[gen_thumb Error] {e}")
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
        # Get random theme
        theme_func = ThemeGenerator.get_random_theme()
        bg, theme_colors = theme_func(base_img)
        
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        canvas.paste(bg, (0, 0))
        
        # Add border glow
        glow_layer = create_dynamic_glow((CANVAS_W, CANVAS_H), 
                                        theme_colors['glow'], 
                                        theme_colors['style'])
        canvas = Image.alpha_composite(canvas, glow_layer)
        
        draw = ImageDraw.Draw(canvas)

        # Create artwork with theme-based shape
        art, thumb_size = create_artwork_shape(base_img, theme_colors['style'])
        
        # Position artwork
        art_x = 80
        art_y = (CANVAS_H - thumb_size) // 2
        
        # Artwork glow ring
        ring_width = 6
        ring_size = thumb_size + ring_width * 4
        ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(ring_img)
        
        for i in range(4):
            offset = i * 8
            alpha = 200 - (i * 40)
            if theme_colors['style'] in ['minimal', 'glass']:
                rdraw.rounded_rectangle(
                    [offset, offset, ring_size - offset, ring_size - offset],
                    radius=60,
                    outline=(*theme_colors['accent'][:3], alpha),
                    width=ring_width
                )
            else:
                rdraw.ellipse(
                    [offset, offset, ring_size - offset, ring_size - offset],
                    outline=(*theme_colors['accent'][:3], alpha),
                    width=ring_width
                )
        
        ring_img = ring_img.filter(ImageFilter.GaussianBlur(6))
        canvas.paste(ring_img, (art_x - ring_width * 2, art_y - ring_width * 2), ring_img)
        canvas.paste(art, (art_x, art_y), art)

        # ShrutiMusic branding
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 45)
        brand_y = 30
        
        # Animated underline effect
        brand_text = "ShrutiMusic"
        brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
        brand_w = brand_bbox[2] - brand_bbox[0]
        
        draw.text((38, brand_y), brand_text, fill=theme_colors['text'], font=brand_font)
        draw.rectangle([35, brand_y + 55, 35 + brand_w, brand_y + 62], 
                      fill=theme_colors['accent'])

        # Text info area
        info_x = art_x + thumb_size + 80
        max_text_w = CANVAS_W - info_x - 50

        # NOW PLAYING with style
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 65)
        np_text = "♪ NOW PLAYING"
        np_y = 140
        
        # Glowing text effect
        for offset in [4, 3, 2]:
            draw.text((info_x + offset, np_y + offset), np_text, 
                     fill=(*theme_colors['accent'][:3], 80), font=np_font)
        draw.text((info_x, np_y), np_text, fill=theme_colors['text'], font=np_font)

        # Title with better spacing
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        title_lines = wrap_text(draw, title, title_font, max_text_w)
        title_text = "\n".join(title_lines)
        title_y = np_y + 90
        
        draw.multiline_text((info_x, title_y), title_text, 
                          fill=theme_colors['text'], font=title_font, spacing=12)

        # Metadata with icons
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 34)
        meta_y = title_y + 150
        line_spacing = 55
        
        duration_label = duration
        if duration and ":" in duration:
            parts = duration.split(":")
            if len(parts) == 2:
                duration_label = f"{parts[0]}m {parts[1]}s"
        
        meta_items = [
            f"👁 {views}",
            f"⏱ {duration_label}",
            f"📺 {channel}"
        ]
        
        for idx, meta in enumerate(meta_items):
            y = meta_y + (idx * line_spacing)
            # Subtle shadow
            draw.text((info_x + 2, y + 2), meta, fill=(0, 0, 0, 120), font=meta_font)
            draw.text((info_x, y), meta, fill=(240, 240, 240, 255), font=meta_font)

        # Decorative elements based on theme
        if theme_colors['style'] in ['neon', 'cyberpunk']:
            # Corner accents
            corner_size = 40
            corner_color = theme_colors['accent']
            draw.line([(20, 20), (20 + corner_size, 20)], fill=corner_color, width=4)
            draw.line([(20, 20), (20, 20 + corner_size)], fill=corner_color, width=4)
            draw.line([(CANVAS_W - 20, 20), (CANVAS_W - 20 - corner_size, 20)], fill=corner_color, width=4)
            draw.line([(CANVAS_W - 20, 20), (CANVAS_W - 20, 20 + corner_size)], fill=corner_color, width=4)

        # Save output
        out = CACHE_DIR / f"{videoid}_premium.png"
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
