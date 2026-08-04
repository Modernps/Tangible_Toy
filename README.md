# Jungle Book Story Narrator

A Python command-line app that creates an original Jungle Book-inspired narration with any chosen subset of seven characters:

- Mowgli
- Baloo
- Bagheera
- Shere Khan
- Kaa
- King Louie
- Akela

The app sends the chosen cast to the Gemini API and asks it to use every selected character while not naming any unselected Jungle Book characters. Once created, ElevenLabs narrates each script line using the configured voice ID for that character.

## Setup

1. Create and activate a virtual environment (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the dependency:

   ```bash
   pip install -r requirements.txt
   ```

3. Set your Gemini API key in the current terminal, or copy `.env.example` to `.env` and put the key there. Never commit the key to the project.

   ```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

4. Run the narrator:

   ```bash
   python3 jungle_book_narrator.py
   ```

When prompted, enter one or more characters by number or name, separated with commas. For example: `1, 2, Kaa`.

After the story is displayed, press `Enter` or type `y` to hear it. Type `n` to skip spoken narration.

## ElevenLabs character voices

Create or choose a voice for the narrator and each of the seven characters in the [ElevenLabs Voice Library or Voice Design tool](https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/voice-design). Copy every resulting `voice_id` to its matching `ELEVENLABS_VOICE_*` variable in `.env`. The app only needs the narrator and voices for the characters selected in a particular story.

To display the voice IDs available to your ElevenLabs account, run:

```bash
python3 jungle_book_narrator.py --list-voices
```

Use one of those exact IDs. A sample ID from online documentation does not automatically belong to your account.

The app applies individual stability, style, and speed settings to every character. Narration is slowed to `0.88` for a child-friendly pace; the character speeds are within ElevenLabs' supported `0.7`–`1.2` range.

For animal sound effects, add your own licensed MP3s to `sound_effects/` with these optional names: `tiger_growl.mp3`, `snake_hiss.mp3`, `bear_grunt.mp3`, `monkey_chatter.mp3`, and `wolf_howl.mp3`. An available sound plays before the matching character speaks.

## Model

By default, the script uses `gemini-3.6-flash`. To select a model available to your account, set `GEMINI_MODEL` before running:

```bash
export GEMINI_MODEL="your-model-name"
```

The script uses Google's official Python SDK and Gemini Generate Content API. See the [Gemini API guide](https://ai.google.dev/gemini-api/docs/generate-content/get-started) for key creation and SDK setup.
