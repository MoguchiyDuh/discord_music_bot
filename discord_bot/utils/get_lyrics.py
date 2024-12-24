import aiohttp
from .config import GENIUS_API_KEY
from bs4 import BeautifulSoup
from dataclasses import dataclass
import re


@dataclass
class Lyrics:
    status: int | None = None
    title: str | None = None
    text: list[str] | None = None
    url: str | None = None
    error_message: str | None = None


async def get_lyrics(track_name: str) -> Lyrics:
    url = f"https://api.genius.com/search?q={track_name}"
    headers = {"Authorization": f"Bearer {GENIUS_API_KEY}"}
    lyrics = Lyrics()

    async with aiohttp.ClientSession() as session:
        try:
            # Search for the track
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    lyrics.status = response.status
                    return lyrics
                data = await response.json()

            track = data.get("response", {}).get("hits", [])
            if not track:
                lyrics.status = 404
                return lyrics

            # Extract track details
            track = track[0]["result"]
            lyrics.status = 200
            lyrics.title = track["full_title"]
            lyrics.url = track["url"]

            # Fetch lyrics page
            async with session.get(lyrics.url) as response:
                if response.status != 200:
                    lyrics.status = response.status
                    return lyrics
                html = await response.text()

            # Parse HTML for lyrics
            soup = BeautifulSoup(html, "html.parser")
            lyrics_divs = soup.find("div", id="lyrics-root").find_all(
                class_="Lyrics-sc-1bcc94c6-1 bzTABU"
            )
            if not lyrics_divs:
                lyrics.error_message = "Lyrics not found on page."
            else:
                # Get track parts for prettier splitting (ex. [Into], [Chorus])
                lyrics_divs_text = [
                    i.get_text(separator="\n", strip=True) for i in lyrics_divs
                ]
                lyrics_divs_text.append(f"\n🔗 Full lyrics: {lyrics.url}")
                chunks = split_track_into_chunks(lyrics_divs_text)
                lyrics.text = chunks

        except aiohttp.ClientError as e:
            lyrics.status = 500
            lyrics.error_message = f"Error fetching data: {str(e)}"

        return lyrics


def split_track_into_chunks(strings: list[str], max_chunk_size=4000) -> list[str]:

    track_parts = []
    for chunk in strings:
        for track_part in chunk.split("["):
            if not track_part:
                continue
            if "]" in track_part:
                track_part = "[" + track_part.strip()

            track_part = track_part
            track_parts.append(track_part)

    chunks = []
    current_chunk = ""
    current_size = 0

    for string in track_parts:
        if current_size + len(string) <= max_chunk_size:
            current_chunk += string + "\n\n"
            current_size += len(string)
        else:
            chunks.append(current_chunk)
            current_chunk = string + "\n\n"
            current_size = len(string)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
