import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ShrutiMusic.utils.formatters import time_to_seconds
import aiohttp
from ShrutiMusic import LOGGER

YOUR_API_URL = None
FALLBACK_API_URL = "https://shrutibots.site"

async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("ShrutiMusic.platforms.Youtube.py")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info("API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
                    logger.info("Using fallback API URL")
    except Exception:
        YOUR_API_URL = FALLBACK_API_URL
        logger.info("Using fallback API URL")

try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass

async def get_video_info(link: str):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            return {
                "title": info.get("title"),
                "duration": info.get("duration", 0),
                "duration_min": f"{info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}",
                "thumbnail": info.get("thumbnail"),
                "id": info.get("id"),
            }
    except:
        return None
    global YOUR_API_URL
    
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            YOUR_API_URL = FALLBACK_API_URL
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}
            
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                download_token = data.get("download_token")
                
                if not download_token:
                    return None
                
                stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=audio"
                
                async with session.get(
                    stream_url,
                    headers={"X-Download-Token": download_token},
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as file_response:
                    if file_response.status != 200:
                        return None
                        
                    with open(file_path, "wb") as f:
                        async for chunk in file_response.content.iter_chunked(16384):
                            f.write(chunk)
                    
                    return file_path

    except Exception:
        return None

async def download_video(link: str) -> str:
    global YOUR_API_URL
    
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            YOUR_API_URL = FALLBACK_API_URL
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}
            
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                download_token = data.get("download_token")
                
                if not download_token:
                    return None
                
                stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=video"
                
                async with session.get(
                    stream_url,
                    headers={"X-Download-Token": download_token},
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as file_response:
                    if file_response.status != 200:
                        return None
                        
                    with open(file_path, "wb") as f:
                        async for chunk in file_response.content.iter_chunked(16384):
                            f.write(chunk)
                    
                    return file_path

    except Exception:
        return None

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        info = await get_video_info(link)
        if not info:
            return None, None, None, None, None
        
        return (
            info["title"],
            info["duration_min"],
            info["duration"],
            info["thumbnail"],
            info["id"]
        )

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        info = await get_video_info(link)
        return info["title"] if info else None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        info = await get_video_info(link)
        return info["duration_min"] if info else None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        info = await get_video_info(link)
        return info["thumbnail"] if info else None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        info = await get_video_info(link)
        if not info:
            return None, None
        
        track_details = {
            "title": info["title"],
            "link": link,
            "vidid": info["id"],
            "duration_min": info["duration_min"],
            "thumb": info["thumbnail"],
        }
        return track_details, info["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "playlistend": 10,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{link}", download=False)
                if "entries" in info:
                    entries = info["entries"]
                    if query_type < len(entries):
                        result = entries[query_type]
                        return (
                            result.get("title"),
                            f"{result.get('duration', 0) // 60}:{result.get('duration', 0) % 60:02d}",
                            result.get("thumbnail"),
                            result.get("id")
                        )
        except:
            pass
        
        return None, None, None, None

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link

        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            
            if downloaded_file:
                return downloaded_file, True
            else:
                return None, False
        except Exception:
            return None, False
