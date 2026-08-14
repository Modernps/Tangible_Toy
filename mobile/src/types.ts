export type Segment = {
  speaker: string;
  text: string;
  sound_effect: string | null;
  audio_base64: string | null;
};

export type NarrateResponse = {
  title: string;
  segments: Segment[];
};

export type StoryLength = "short" | "medium" | "long";
