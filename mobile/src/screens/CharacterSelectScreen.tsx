import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { fetchCharacters, fetchNarration } from "../api";
import { defaultBackendUrl, getBackendUrl, setBackendUrl } from "../config";
import type { NarrateResponse, StoryLength } from "../types";

type Props = {
  onStoryReady: (story: NarrateResponse, backendUrl: string) => void;
};

const LENGTHS: StoryLength[] = ["short", "medium", "long"];

export default function CharacterSelectScreen({ onStoryReady }: Props) {
  const [backendUrl, setBackendUrlValue] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [characters, setCharacters] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [length, setLength] = useState<StoryLength>("medium");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const url = await getBackendUrl();
      setBackendUrlValue(url);
      setCharacters(await fetchCharacters(url));
    })();
  }, []);

  const toggleCharacter = (name: string) => {
    setSelected((current) =>
      current.includes(name)
        ? current.filter((item) => item !== name)
        : [...current, name]
    );
  };

  const handleSaveBackendUrl = async (url: string) => {
    setBackendUrlValue(url);
    await setBackendUrl(url);
    setCharacters(await fetchCharacters(url || defaultBackendUrl()));
  };

  const handleCreateStory = async () => {
    if (!selected.length || loading) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const story = await fetchNarration(backendUrl, selected, length);
      onStoryReady(story, backendUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.heading}>Jungle Book Story Narrator</Text>
      <Text style={styles.subheading}>
        Pick your cast, then create an original narrated story.
      </Text>

      <View style={styles.chipRow}>
        {characters.map((name) => {
          const isSelected = selected.includes(name);
          return (
            <TouchableOpacity
              key={name}
              style={[styles.chip, isSelected && styles.chipSelected]}
              onPress={() => toggleCharacter(name)}
            >
              <Text
                style={[styles.chipText, isSelected && styles.chipTextSelected]}
              >
                {name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <Text style={styles.sectionLabel}>Story length</Text>
      <View style={styles.chipRow}>
        {LENGTHS.map((option) => (
          <TouchableOpacity
            key={option}
            style={[styles.lengthChip, length === option && styles.chipSelected]}
            onPress={() => setLength(option)}
          >
            <Text
              style={[
                styles.chipText,
                length === option && styles.chipTextSelected,
              ]}
            >
              {option}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <TouchableOpacity
        style={[styles.createButton, (!selected.length || loading) && styles.createButtonDisabled]}
        onPress={handleCreateStory}
        disabled={!selected.length || loading}
      >
        {loading ? (
          <ActivityIndicator color="#0f1f16" />
        ) : (
          <Text style={styles.createButtonText}>Create story</Text>
        )}
      </TouchableOpacity>
      {loading ? (
        <Text style={styles.loadingHint}>
          Writing the story and recording each character's voice — this can
          take up to a minute.
        </Text>
      ) : null}

      <TouchableOpacity
        style={styles.settingsToggle}
        onPress={() => setShowSettings((value) => !value)}
      >
        <Text style={styles.settingsToggleText}>
          {showSettings ? "Hide" : "Show"} backend settings
        </Text>
      </TouchableOpacity>

      {showSettings ? (
        <View style={styles.settingsBox}>
          <Text style={styles.sectionLabel}>Backend URL</Text>
          <TextInput
            style={styles.input}
            value={backendUrl}
            onChangeText={handleSaveBackendUrl}
            placeholder={defaultBackendUrl()}
            placeholderTextColor="#6b7d70"
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Text style={styles.settingsHint}>
            Address of the FastAPI backend running on your computer. Defaults
            fit the iOS Simulator/web ({defaultBackendUrl()}); Android
            emulators need 10.0.2.2, and a physical device needs your
            computer's LAN IP.
          </Text>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    paddingTop: 64,
    gap: 12,
  },
  heading: {
    fontSize: 26,
    fontWeight: "700",
    color: "#f2f7f3",
  },
  subheading: {
    fontSize: 15,
    color: "#b7c9bb",
    marginBottom: 12,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#8fa895",
    textTransform: "uppercase",
    marginTop: 8,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#3a5240",
    backgroundColor: "#16281c",
  },
  lengthChip: {
    paddingVertical: 8,
    paddingHorizontal: 18,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#3a5240",
    backgroundColor: "#16281c",
  },
  chipSelected: {
    backgroundColor: "#e8c468",
    borderColor: "#e8c468",
  },
  chipText: {
    color: "#dfeee2",
    fontSize: 14,
  },
  chipTextSelected: {
    color: "#0f1f16",
    fontWeight: "700",
  },
  createButton: {
    marginTop: 20,
    backgroundColor: "#e8c468",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
  createButtonDisabled: {
    opacity: 0.5,
  },
  createButtonText: {
    color: "#0f1f16",
    fontWeight: "700",
    fontSize: 16,
  },
  loadingHint: {
    color: "#8fa895",
    fontSize: 12,
    textAlign: "center",
    marginTop: 8,
  },
  error: {
    color: "#f2a1a1",
    fontSize: 13,
    marginTop: 4,
  },
  settingsToggle: {
    marginTop: 28,
    alignSelf: "flex-start",
  },
  settingsToggleText: {
    color: "#8fa895",
    fontSize: 13,
    textDecorationLine: "underline",
  },
  settingsBox: {
    marginTop: 10,
    gap: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: "#3a5240",
    backgroundColor: "#16281c",
    color: "#f2f7f3",
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    fontSize: 14,
  },
  settingsHint: {
    color: "#728478",
    fontSize: 11,
    lineHeight: 16,
  },
});
