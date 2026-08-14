"""FastAPI backend for the Jungle Book Story Narrator mobile app.

Wraps the existing CLI's story generation and text-to-speech logic behind an
HTTP API so a mobile client never needs the Gemini/ElevenLabs API keys.
"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jungle_book_narrator as narrator  # noqa: E402

app = FastAPI(title="Jungle Book Story Narrator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves the same sound_effects/*.mp3 files the CLI plays locally, so the
# mobile app can fetch them by name instead of bundling audio assets.
SOUND_EFFECTS_DIR = Path(__file__).resolve().parent.parent / "sound_effects"
if SOUND_EFFECTS_DIR.is_dir():
    app.mount(
        "/sound-effects",
        StaticFiles(directory=str(SOUND_EFFECTS_DIR)),
        name="sound-effects",
    )

TITLE_PATTERN = re.compile(r"^TITLE:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


class NarrateRequest(BaseModel):
    characters: list[str]
    length: Literal["short", "medium", "long"] = "medium"
    include_audio: bool = True


class Segment(BaseModel):
    speaker: str
    text: str
    sound_effect: str | None = None
    audio_base64: str | None = None


class NarrateResponse(BaseModel):
    title: str
    segments: list[Segment]


def extract_title(story: str) -> str:
    match = TITLE_PATTERN.search(story)
    return match.group(1).strip() if match else "Jungle Book Story"


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/characters")
def get_characters() -> list[str]:
    return list(narrator.CHARACTERS)


@app.get("/api/voices")
def get_voices() -> list[dict[str, str]]:
    try:
        return narrator.list_available_voices()
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/narrate", response_model=NarrateResponse)
def narrate(request: NarrateRequest) -> NarrateResponse:
    try:
        cast = narrator.parse_characters(", ".join(request.characters))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    try:
        story = narrator.generate_story(cast, request.length)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    segments: list[Segment] = []
    for speaker, text in narrator.split_story_segments(story):
        audio_b64 = None
        if request.include_audio:
            try:
                audio_bytes = narrator.synthesize_speech(text, speaker)
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            except RuntimeError:
                # Voice not configured or the TTS call failed; keep the text,
                # skip audio for this line rather than failing the whole story.
                pass
        segments.append(
            Segment(
                speaker=speaker,
                text=text,
                sound_effect=narrator.SOUND_EFFECTS.get(speaker),
                audio_base64=audio_b64,
            )
        )

    return NarrateResponse(title=extract_title(story), segments=segments)
