import asyncio
import discord
import yt_dlp

from . import Playlist, Track


# --------------------------------------------------
class TrackSelectButton(discord.ui.Button):
    def __init__(self, label, track: Track):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.track = track

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_track = self.track
        await interaction.response.defer()
        self.view.stop()


class TrackSelectView(discord.ui.View):
    def __init__(self, tracks: list[Track]):
        super().__init__(timeout=60)
        self.selected_track = None
        for i, track in enumerate(tracks, start=1):
            self.add_item(TrackSelectButton(label=str(i), track=track))


# --------------------------------------------------


class YTSource:
    """YouTube audio source using yt-dlp (for both single song and playlists)."""

    YTDL_OPTIONS = {
        "no_warnings": True,  # Suppress warnings
        "skip_download": True,  # Don't download anything
        "extract_flat": True,  # Only extract metadata (e.g., title, duration, thumbnail)
        "format": "bestaudio/best",  # For best audio info (doesn't affect title, duration, or thumbnail)
        "noplaylist": False,  # Keep playlist support
    }
    ENTRIES_COUNT = 5  # Number of entries to fetch for search queries

    async def fetch_track_by_url(self, url) -> Track:
        """Fetches a single song by url"""

        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(self.YTDL_OPTIONS) as ytdl:
            track = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(url, download=False)
            )
            return self.__get_track(track)

    def __get_track(self, entry) -> Track:
        return Track(
            title=entry.get("title", "Unknown Title"),
            duration=entry.get("duration", 0),
            webpage_url=entry.get("webpage_url", entry.get("url")),
            audio_url=entry.get("url", ""),
            thumbnail=entry.get("thumbnail", ""),
        )

    async def fetch_playlist(self, url) -> Playlist:
        """Fetches a playlist"""
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(self.YTDL_OPTIONS) as ytdl:
            entries = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(url, download=False)
            )
            return Playlist(
                title=entries.get("title", "Unknown Title"),
                webpage_url=entries.get("webpage_url"),
                tracks=[self.__get_track(entry) for entry in entries["entries"]],
            )

    async def fetch_track_by_name(self, name) -> list[Track]:
        """Fetches a single song by name"""
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(self.YTDL_OPTIONS) as ytdl:
            entries = await loop.run_in_executor(
                None,
                lambda: ytdl.extract_info(
                    f"ytsearch{self.ENTRIES_COUNT}:{name}", download=False
                ),
            )
        return [self.__get_track(entry) for entry in entries["entries"]]
