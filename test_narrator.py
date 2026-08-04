import os
import unittest
from unittest.mock import patch

from jungle_book_narrator import (
    build_prompt,
    generate_story,
    list_available_voices,
    parse_characters,
    speak_story,
    split_story_segments,
)


class FakeModels:
    def generate_content(self, **kwargs):
        self.request = kwargs
        return type("Response", (), {"text": "A Jungle Adventure"})()


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


class NarratorTests(unittest.TestCase):
    def test_parse_characters_supports_numbers_and_names(self):
        self.assertEqual(
            parse_characters("1, Baloo, kaa, 1"),
            ["Mowgli", "Baloo", "Kaa"],
        )

    def test_parse_characters_rejects_unknown_character(self):
        with self.assertRaises(ValueError):
            parse_characters("Mowgli, Robin Hood")

    def test_prompt_limits_the_cast(self):
        prompt = build_prompt(["Baloo", "Kaa"])
        self.assertIn("Baloo, Kaa", prompt)
        self.assertIn("Do not introduce", prompt)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    def test_generate_story_uses_gemini_api(self):
        client = FakeClient()
        story = generate_story(["Mowgli"], client=client)
        self.assertEqual(story, "A Jungle Adventure")
        self.assertEqual(client.models.request["model"], os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))

    @patch("jungle_book_narrator.play_audio")
    @patch("jungle_book_narrator.synthesize_speech", return_value=b"audio")
    @patch("jungle_book_narrator.play_sound_effect")
    def test_speak_story_uses_character_voices(self, effects_mock, speech_mock, audio_mock):
        speak_story("NARRATOR: Night fell.\nMowgli: I can help!")
        self.assertEqual(
            [call.args[1] for call in speech_mock.call_args_list],
            ["NARRATOR", "Mowgli"],
        )
        self.assertEqual(audio_mock.call_count, 2)
        self.assertEqual(effects_mock.call_count, 2)

    def test_split_story_segments_uses_narrator_for_unknown_labels(self):
        self.assertEqual(
            split_story_segments("Mowgli: Hello\nUnknown: Hello again"),
            [("Mowgli", "Hello"), ("NARRATOR", "Hello again")],
        )

    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key"})
    @patch("jungle_book_narrator.urlopen")
    def test_list_available_voices(self, urlopen_mock):
        response = type("Response", (), {"__enter__": lambda self: self, "__exit__": lambda *args: None})()
        urlopen_mock.return_value = response
        with patch("jungle_book_narrator.json.load", return_value={"voices": [{"name": "Narrator", "voice_id": "voice-1"}]}):
            self.assertEqual(list_available_voices(), [{"name": "Narrator", "voice_id": "voice-1"}])


if __name__ == "__main__":
    unittest.main()
