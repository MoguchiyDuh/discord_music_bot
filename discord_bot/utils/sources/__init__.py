from dataclasses import dataclass
from discord import FFmpegPCMAudio


@dataclass
class Track:
    """Represents a song with title, duration, thumbnail, and URL."""

    title: str
    duration: int  # Duration in seconds
    webpage_url: str  # webpage url
    audio_url: FFmpegPCMAudio
    thumbnail: str | None = None  # Optional thumbnail image URL

    def __repr__(self):
        return self.title

    def __str__(self):
        return (
            f"Title: [{self.title}](<{self.webpage_url}>)\nDuration: {self.duration}s"
        )


@dataclass
class Playlist:
    """Represents a playlist with title, duration, thumbnail, and URL."""

    title: str
    webpage_url: str
    tracks: list[Track]

    @property
    def duration(self) -> int:
        return sum([song.duration for song in self.tracks])

    @property
    def length(self) -> int:
        return sum(len(self.tracks))

    def __repr__(self):
        return self.title

    def __str__(self):
        return f"Playlist Title: [{self.title}](<{self.webpage_url}>)\nDuration: {self.duration}s\nSongs Count: {self.length}"
