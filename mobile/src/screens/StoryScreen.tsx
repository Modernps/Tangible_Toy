import { useCallback, useEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { createAudioPlayer, useAudioPlayer } from "expo-audio";
import type { NarrateResponse } from "../types";

type Props = {
  story: NarrateResponse;
  backendUrl: string;
  onBack: () => void;
};

/** Plays one short clip (e.g. an animal sound effect) and resolves once it
 * finishes, times out, or fails to load — so a missing sound effect never
 * blocks the story from continuing. */
function playClipAndWait(uri: string, timeoutMs = 2500): Promise<void> {
  return new Promise((resolve) => {
    let settled = false;
    const player = createAudioPlayer({ uri });
    const finish = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      subscription.remove();
      player.remove();
      resolve();
    };
    const subscription = player.addListener("playbackStatusUpdate", (status) => {
      if (status.didJustFinish) finish();
    });
    const timer = setTimeout(finish, timeoutMs);
    player.play();
  });
}

export default function StoryScreen({ story, backendUrl, onBack }: Props) {
  const { title, segments } = story;
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const player = useAudioPlayer(null);

  const indexRef = useRef(currentIndex);
  const playingRef = useRef(isPlaying);
  indexRef.current = currentIndex;
  playingRef.current = isPlaying;

  const playSegmentAt = useCallback(
    async (index: number) => {
      if (index >= segments.length) {
        setIsPlaying(false);
        setCurrentIndex(-1);
        return;
      }
      setCurrentIndex(index);
      indexRef.current = index;
      const segment = segments[index];

      if (segment.sound_effect) {
        await playClipAndWait(`${backendUrl}/sound-effects/${segment.sound_effect}`);
      }
      // Playback may have been stopped, or a different segment requested,
      // while the sound effect above was playing.
      if (!playingRef.current || indexRef.current !== index) {
        return;
      }

      if (segment.audio_base64) {
        player.replace({ uri: `data:audio/mpeg;base64,${segment.audio_base64}` });
        player.play();
      } else {
        setTimeout(() => {
          if (playingRef.current) playSegmentAt(index + 1);
        }, 900);
      }
    },
    [segments, backendUrl, player]
  );

  useEffect(() => {
    const subscription = player.addListener("playbackStatusUpdate", (status) => {
      if (status.didJustFinish && playingRef.current) {
        playSegmentAt(indexRef.current + 1);
      }
    });
    return () => subscription.remove();
  }, [player, playSegmentAt]);

  const handlePlayPause = () => {
    if (isPlaying) {
      player.pause();
      setIsPlaying(false);
      return;
    }
    playingRef.current = true;
    setIsPlaying(true);
    if (currentIndex === -1) {
      playSegmentAt(0);
    } else {
      player.play();
    }
  };

  const handleRestart = () => {
    setIsPlaying(true);
    playSegmentAt(0);
  };

  const missingVoiceCount = segments.filter((segment) => !segment.audio_base64).length;

  return (
    <View style={styles.container}>
      <TouchableOpacity onPress={onBack} style={styles.backButton}>
        <Text style={styles.backButtonText}>‹ New story</Text>
      </TouchableOpacity>

      <Text style={styles.title}>{title}</Text>

      {missingVoiceCount > 0 ? (
        <Text style={styles.notice}>
          {missingVoiceCount} line{missingVoiceCount === 1 ? "" : "s"} will
          play as text only — add that character's ElevenLabs voice ID to
          hear it spoken.
        </Text>
      ) : null}

      <ScrollView style={styles.script} contentContainerStyle={styles.scriptContent}>
        {segments.map((segment, index) => (
          <View
            key={index}
            style={[styles.line, index === currentIndex && styles.lineActive]}
          >
            <Text style={styles.speaker}>{segment.speaker}</Text>
            <Text style={styles.text}>{segment.text}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={styles.controls}>
        <TouchableOpacity style={styles.controlButton} onPress={handleRestart}>
          <Text style={styles.controlButtonText}>Restart</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.controlButton, styles.playButton]}
          onPress={handlePlayPause}
        >
          <Text style={styles.playButtonText}>
            {isPlaying ? "Pause" : currentIndex === -1 ? "Play" : "Resume"}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 64,
    paddingHorizontal: 20,
  },
  backButton: {
    marginBottom: 12,
  },
  backButtonText: {
    color: "#8fa895",
    fontSize: 14,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#f2f7f3",
    marginBottom: 8,
  },
  notice: {
    color: "#e8c468",
    fontSize: 12,
    marginBottom: 8,
  },
  script: {
    flex: 1,
  },
  scriptContent: {
    paddingBottom: 16,
    gap: 10,
  },
  line: {
    padding: 10,
    borderRadius: 8,
  },
  lineActive: {
    backgroundColor: "#1d3324",
  },
  speaker: {
    color: "#e8c468",
    fontSize: 12,
    fontWeight: "700",
    marginBottom: 2,
  },
  text: {
    color: "#dfeee2",
    fontSize: 15,
    lineHeight: 21,
  },
  controls: {
    flexDirection: "row",
    gap: 10,
    paddingVertical: 16,
  },
  controlButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    backgroundColor: "#16281c",
    borderWidth: 1,
    borderColor: "#3a5240",
  },
  controlButtonText: {
    color: "#dfeee2",
    fontWeight: "600",
  },
  playButton: {
    backgroundColor: "#e8c468",
    borderColor: "#e8c468",
  },
  playButtonText: {
    color: "#0f1f16",
    fontWeight: "700",
  },
});
