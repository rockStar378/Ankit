import asyncio
import os
import re
import json
from typing import Union
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from ShrutiMusic.utils.database import is_on_off
from ShrutiMusic import app
from ShrutiMusic.utils.formatters import time_to_seconds
import random
import logging
import aiohttp
from ShrutiMusic import LOGGER
from urllib.parse import urlparse

YOUR_API_URL = None

async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa") as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info(f"API URL loaded successfully")
                else:
                    logger.error(f"Failed to fetch API URL. HTTP Status: {response.status}")
    except Exception as e:
        logger.error(f"Error loading API URL: {e}")

try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass

async def get_telegram_file(telegram_link: str, video_id: str, file_type: str) -> str:
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    try:
        extension = ".webm" if file_type == "audio" else ".mkv"
        file_path = os.path.join("downloads", f"{video_id}{extension}")
        
        if os.path.exists(file_path):
            logger.info(f"File exists: {video_id}")
            return file_path
        
        parsed = urlparse(telegram_link)
        parts = parsed.path.strip("/").split("/")
        
        if len(parts) < 2:
            logger.error(f"Invalid Telegram link format: {telegram_link}")
            return None
            
        channel_name = parts[0]
        message_id = int(parts[1])
        
        logger.info(f"Downloading from @{channel_name}/{message_id}")
        
        msg = await app.get_messages(channel_name, message_id)
        os.makedirs("downloads", exist_ok=True)
        await msg.download(file_name=file_path)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f"Downloaded: {video_id}")
            return file_path
        else:
            logger.error(f"Failed: {video_id}")
            return None
        
    except Exception as e:
        logger.error(f"Failed to download {video_id}: {e}")
        return None

async def parallel_download(session, url, file_path, logger):
    try:
        async with session.head(url) as head:
            if head.status != 200:
                return await fast_sequential(session, url, file_path, logger)
            
            total_size = int(head.headers.get('Content-Length', 0))
            accepts_ranges = head.headers.get('Accept-Ranges') == 'bytes'
        
        if not accepts_ranges or total_size < CHUNK_SIZE * 2:
            return await fast_sequential(session, url, file_path, logger)
        
        with open(file_path, 'wb') as f:
            f.truncate(total_size)
        
        num_chunks = min(MAX_CONCURRENT, (total_size // CHUNK_SIZE) + 1) if MAX_CONCURRENT > 0 else (total_size // CHUNK_SIZE) + 1
        chunk_size = total_size // num_chunks
        
        async def dl_chunk(start, end):
            headers = {'Range': f'bytes={start}-{end}'}
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 206):
                    data = await resp.read()
                    with open(file_path, 'r+b') as f:
                        f.seek(start)
                        f.write(data)
                    return True
                return False
        
        tasks = []
        for i in range(num_chunks):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < num_chunks - 1 else total_size - 1
            tasks.append(dl_chunk(start, end))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if all(r is True for r in results):
            logger.info(f"Parallel download complete")
            return True
        else:
            return await fast_sequential(session, url, file_path, logger)
            
    except Exception as e:
        logger.error(f"Parallel error: {e}")
        return await fast_sequential(session, url, file_path, logger)

async def fast_sequential(session, url, file_path, logger):
    try:
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f"HTTP {response.status}")
                return False
            
            with open(file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    f.write(chunk)
            
            return True
    except Exception as e:
        logger.error(f"Sequential error: {e}")
        return False

async def download_song(link: str) -> str:
    global YOUR_API_URL
    
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
            logger.error("API URL not available")
            return None
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    logger.info(f"Starting audio download: {video_id}")

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")

    if os.path.exists(file_path):
        logger.info(f"File exists: {video_id}")
        return file_path

    try:
        connector = aiohttp.TCPConnector(limit=0, force_close=False, enable_cleanup_closed=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            params = {"url": video_id, "type": "audio"}
            
            async with session.get(f"{YOUR_API_URL}/download", params=params) as response:
                data = await response.json()

                if response.status != 200:
                    logger.error(f"API error: {response.status}")
                    return None

                if data.get("link") and "t.me" in str(data.get("link")):
                    telegram_link = data["link"]
                    logger.info(f"Telegram link received: {telegram_link}")
                    
                    downloaded_file = await get_telegram_file(telegram_link, video_id, "audio")
                    if downloaded_file:
                        return downloaded_file
                    else:
                        logger.warning(f"Telegram download failed")
                        return None
                
                elif data.get("status") == "success" and data.get("stream_url"):
                    stream_url = data["stream_url"]
                    logger.info(f"Stream URL obtained: {video_id}")
                    
                    success = await parallel_download(session, stream_url, file_path, logger)
                    
                    if success:
                        logger.info(f"Downloaded: {video_id}")
                        return file_path
                    else:
                        logger.error(f"Download failed: {video_id}")
                        return None
                else:
                    logger.error(f"Invalid response: {data}")
                    return None

    except Exception as e:
        logger.error(f"Exception: {video_id} - {e}")
        return None


async def download_video(link: str) -> str:
    global YOUR_API_URL
    
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
            logger.error("API URL not available")
            return None
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    logger.info(f"Starting video download: {video_id}")

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mkv")

    if os.path.exists(file_path):
        logger.info(f"File exists: {video_id}")
        return file_path

    try:
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, force_close=False, enable_cleanup_closed=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            params = {"url": video_id, "type": "video"}
            
            async with session.get(f"{YOUR_API_URL}/download", params=params) as response:
                data = await response.json()

                if response.status != 200:
                    logger.error(f"API error: {response.status}")
                    return None

                if data.get("link") and "t.me" in str(data.get("link")):
                    telegram_link = data["link"]
                    logger.info(f"Telegram link received: {telegram_link}")
                    
                    downloaded_file = await get_telegram_file(telegram_link, video_id, "video")
                    if downloaded_file:
                        return downloaded_file
                    else:
                        logger.warning(f"Telegram download failed")
                        return None
                
                elif data.get("status") == "success" and data.get("stream_url"):
                    stream_url = data["stream_url"]
                    logger.info(f"Stream URL obtained: {video_id}")
                    
                    success = await parallel_download(session, stream_url, file_path, logger)
                    
                    if success:
                        logger.info(f"Downloaded: {video_id}")
                        return file_path
                    else:
                        logger.error(f"Download failed: {video_id}")
                        return None
                else:
                    logger.error(f"Invalid response: {data}")
                    return None

    except Exception as e:
        logger.error(f"Exception: {video_id} - {e}")
        return None

async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

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
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

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
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

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
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

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
            if songvideo or songaudio:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            elif video:
                downloaded_file = await download_video(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            else:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
        except Exception as e:
            print(f"Download failed: {e}")
            return None, False
