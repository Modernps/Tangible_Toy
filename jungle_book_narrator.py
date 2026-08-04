"""Create a Jungle Book narration from a user-selected cast."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import json

try:
    import google.genai as genai  # type: ignore[import-not-found]
except ImportError:
    genai = None


def load_local_env() -> None:
    """Load simple KEY=value entries from the .env file beside this script."""
    env_file = Path(__file__).with_name(".env")
    if not env_file.is_file():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        if key:
            os.environ.setdefault(key, value.strip().strip('"\''))


load_local_env()

CHARACTERS = (
    "Mowgli",
    "Baloo",
    "Bagheera",
    "Shere Khan",
    "Kaa",
    "King Louie",
    "Akela",
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# Voice IDs belong to the user's ElevenLabs library, so they are configured in .env.
VOICE_ID_ENV = {
    "NARRATOR": "ELEVENLABS_VOICE_NARRATOR",
    "Mowgli": "ELEVENLABS_VOICE_MOWGLI",
    "Baloo": "ELEVENLABS_VOICE_BALOO",
    "Bagheera": "ELEVENLABS_VOICE_BAGHEERA",
    "Shere Khan": "ELEVENLABS_VOICE_SHERE_KHAN",
    "Kaa": "ELEVENLABS_VOICE_KAA",
    "King Louie": "ELEVENLABS_VOICE_KING_LOUIE",
    "Akela": "ELEVENLABS_VOICE_AKELA",
}

# All speeds are within ElevenLabs' 0.7-1.2 supported range.
SPEAKER_SETTINGS = {
    "NARRATOR": {"speed": 0.88, "stability": 0.55, "style": 0.20},
    "Mowgli": {"speed": 1.02, "stability": 0.40, "style": 0.40},
    "Baloo": {"speed": 0.86, "stability": 0.50, "style": 0.35},
    "Bagheera": {"speed": 0.88, "stability": 0.65, "style": 0.20},
    "Shere Khan": {"speed": 0.80, "stability": 0.70, "style": 0.35},
    "Kaa": {"speed": 0.76, "stability": 0.45, "style": 0.45},
    "King Louie": {"speed": 1.05, "stability": 0.35, "style": 0.50},
    "Akela": {"speed": 0.84, "stability": 0.70, "style": 0.20},
}

SOUND_EFFECTS = {
    "Baloo": "bear_grunt.mp3",
    "Kaa": "snake_hiss.mp3",
    "Shere Khan": "tiger_growl.mp3",
    "King Louie": "monkey_chatter.mp3",
    "Akela": "wolf_howl.mp3",
}


def display_character_menu() -> None:
    print("\nAvailable Jungle Book characters:")
    for number, character in enumerate(CHARACTERS, start=1):
        print(f"  {number}. {character}")


def parse_characters(selection: str) -> list[str]:
    """Turn comma-separated character names or menu numbers into a unique cast."""
    if not selection.strip():
        raise ValueError("Choose at least one character.")

    lookup = {name.casefold(): name for name in CHARACTERS}
    cast: list[str] = []
    invalid: list[str] = []

    for item in selection.split(","):
        choice = item.strip()
        if not choice:
            continue

        if choice.isdigit() and 1 <= int(choice) <= len(CHARACTERS):
            character = CHARACTERS[int(choice) - 1]
        else:
            character = lookup.get(choice.casefold())

        if character is None:
            invalid.append(choice)
        elif character not in cast:
            cast.append(character)

    if invalid:
        raise ValueError(f"Unknown character(s): {', '.join(invalid)}")
    if not cast:
        raise ValueError("Choose at least one valid character.")
    return cast


def build_prompt(characters: Iterable[str], length: str = "medium") -> str:
    cast = list(characters)
    cast_text = ", ".join(cast)
    return f"""Write an original, child-friendly Jungle Book-inspired story narration.

Use only these characters as named story characters: {cast_text}.
Do not introduce or name any other Jungle Book characters. Give every selected
character a meaningful role. Set the story in an original jungle adventure,
with a warm, vivid narrator voice, clear beginning, middle, and ending, and a
gentle positive lesson. Avoid quoting or closely retelling any existing book,
film, or song. Make it {length} in length (about 500-700 words for medium).

Return a read-aloud script in exactly this format, without Markdown:
TITLE: a short title
NARRATOR: narration
Character Name: spoken dialogue or narration

Every non-empty line after the title must begin with `NARRATOR:` or the name
of a selected character followed by a colon. Use only selected character names
as labels. Include several short lines of dialogue when characters are selected
so their distinct voices can be heard."""


def generate_story(characters: list[str], length: str = "medium", client: Any | None = None) -> str:
    """Request a story from the Gemini Generate Content API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your environment and try again."
        )
    if client is None and genai is None:
        raise RuntimeError("Gemini SDK is not installed. Run: pip install -r requirements.txt")

    if client is not None:
        response = client.models.generate_content(
            model=MODEL,
            contents=build_prompt(characters, length),
        )
        story = (response.text or "").strip()
    elif hasattr(genai, "Client"):
        api_client = genai.Client(api_key=api_key)
        response = api_client.models.generate_content(
            model=MODEL,
            contents=build_prompt(characters, length),
        )
        story = (response.text or "").strip()
    elif hasattr(genai, "GenerativeModel"):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(build_prompt(characters, length))
        story = (response.text or "").strip()
    else:
        genai.configure(api_key=api_key)
        response = genai.generate_text(prompt=build_prompt(characters, length))
        story = (getattr(response, "result", None) or getattr(response, "text", "") or "").strip()
    if not story:
        raise RuntimeError("The API returned an empty story. Please try again.")
    return story


def split_story_segments(story: str) -> list[tuple[str, str]]:
    """Extract labelled script lines, using the narrator voice as a safe fallback."""
    speakers = {speaker.casefold(): speaker for speaker in VOICE_ID_ENV}
    segments: list[tuple[str, str]] = []

    for raw_line in story.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^([^:]+):\s*(.+)$", line)
        if not match:
            segments.append(("NARRATOR", line))
            continue

        label, text = match.groups()
        speaker = speakers.get(label.strip().casefold(), "NARRATOR")
        if label.strip().casefold() == "title":
            text = f"{text}."
        segments.append((speaker, text))

    return segments


def get_voice_id(speaker: str) -> str:
    environment_name = VOICE_ID_ENV[speaker]
    voice_id = os.getenv(environment_name, "").strip()
    if not voice_id or voice_id.startswith("paste_"):
        raise RuntimeError(
            f"{environment_name} is not configured. Add this character's ElevenLabs voice ID to .env."
        )
    return voice_id


def list_available_voices() -> list[dict[str, str]]:
    """Return the voices available to the configured ElevenLabs account."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set. Add it to .env first.")

    request = Request(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key},
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Could not list ElevenLabs voices ({error.code}): {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to ElevenLabs: {error.reason}") from error

    return [
        {"name": voice.get("name", "Unnamed"), "voice_id": voice["voice_id"]}
        for voice in data.get("voices", [])
        if "voice_id" in voice
    ]


def print_available_voices() -> None:
    voices = list_available_voices()
    if not voices:
        print("No voices are available in this ElevenLabs account.")
        return
    print("Available ElevenLabs voices:")
    for voice in voices:
        print(f"- {voice['name']}: {voice['voice_id']}")


def synthesize_speech(text: str, speaker: str) -> bytes:
    """Generate one MP3 segment with the speaker's ElevenLabs voice."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set. Add it to .env to enable character voices.")

    settings = SPEAKER_SETTINGS[speaker]
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": settings["stability"],
            "similarity_boost": 0.75,
            "style": settings["style"],
            "use_speaker_boost": True,
            "speed": settings["speed"],
        },
    }
    request = Request(
        "https://api.elevenlabs.io/v1/text-to-speech/"
        f"{quote(get_voice_id(speaker))}?output_format=mp3_44100_128",
        data=json.dumps(payload).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            return response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ElevenLabs request failed ({error.code}): {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to ElevenLabs: {error.reason}") from error


def play_audio_file(file_path: str) -> None:
    """Play an audio file cross-platform (Windows, macOS, Linux)."""
    if sys.platform == "win32":
        import ctypes
        path_str = str(Path(file_path).resolve())
        mci = ctypes.windll.winmm.mciSendStringW
        mci(f'open "{path_str}" type mpegvideo alias mp3_play', None, 0, 0)
        mci("play mp3_play wait", None, 0, 0)
        mci("close mp3_play", None, 0, 0)
    elif sys.platform == "darwin":
        subprocess.run(["afplay", str(file_path)], check=True)
    else:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(file_path)], check=True)


def play_audio(audio: bytes) -> None:
    """Play an MP3 byte stream cross-platform, deleting the temporary file afterwards."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
        temp_path = audio_file.name
        audio_file.write(audio)

    try:
        play_audio_file(temp_path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def play_sound_effect(speaker: str) -> None:
    """Optionally play a local animal sound before that character speaks."""
    effect_name = SOUND_EFFECTS.get(speaker)
    if not effect_name:
        return
    effect_path = Path(__file__).with_name("sound_effects") / effect_name
    if effect_path.is_file():
        play_audio_file(str(effect_path))


def speak_story(story: str) -> None:
    """Play each script line through its ElevenLabs character voice."""
    for speaker, text in split_story_segments(story):
        play_sound_effect(speaker)
        play_audio(synthesize_speech(text, speaker))


def main() -> None:
    if "--list-voices" in sys.argv:
        try:
            print_available_voices()
        except RuntimeError as error:
            print(error)
        return

    print("Jungle Book Story Narrator")
    print("Choose one or more of the seven characters to create and hear a custom story.")
    display_character_menu()
    selection = input("\nEnter names or numbers separated by commas (example: 1, 2, Kaa): ")

    try:
        cast = parse_characters(selection)
        print(f"\nCreating a story featuring: {', '.join(cast)}...\n")
        story = generate_story(cast)
        print(story)
        play_narration = input("\nPlay the spoken narration? [Y/n]: ").strip().casefold()
        if play_narration in {"", "y", "yes"}:
            print("\nPlaying narration...\n")
            speak_story(story)
    except ValueError as error:
        print(f"Selection error: {error}")
    except RuntimeError as error:
        print(error)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Could not play narration: {error}")
    except Exception as error:
        print(f"Gemini API error: {error}")


if __name__ == "__main__":
    main()
