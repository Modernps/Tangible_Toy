import type { NarrateResponse, StoryLength } from "./types";

const FALLBACK_CHARACTERS = [
  "Mowgli",
  "Baloo",
  "Bagheera",
  "Shere Khan",
  "Kaa",
  "King Louie",
  "Akela",
];

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Response wasn't JSON; fall through to the status text below.
  }
  return `${response.status} ${response.statusText}`;
}

export async function fetchCharacters(backendUrl: string): Promise<string[]> {
  try {
    const response = await fetch(`${backendUrl}/api/characters`);
    if (!response.ok) {
      return FALLBACK_CHARACTERS;
    }
    const characters = await response.json();
    return Array.isArray(characters) && characters.length
      ? characters
      : FALLBACK_CHARACTERS;
  } catch {
    return FALLBACK_CHARACTERS;
  }
}

export async function fetchNarration(
  backendUrl: string,
  characters: string[],
  length: StoryLength
): Promise<NarrateResponse> {
  const response = await fetch(`${backendUrl}/api/narrate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ characters, length, include_audio: true }),
  });

  if (!response.ok) {
    throw new Error(await readErrorDetail(response));
  }

  return response.json();
}
