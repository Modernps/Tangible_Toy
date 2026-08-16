import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import CharacterSelectScreen from './src/screens/CharacterSelectScreen';
import StoryScreen from './src/screens/StoryScreen';
import type { NarrateResponse } from './src/types';

export default function App() {
  const [story, setStory] = useState<NarrateResponse | null>(null);
  const [storyBackendUrl, setStoryBackendUrl] = useState('');

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="light" />
        {story ? (
          <StoryScreen
            story={story}
            backendUrl={storyBackendUrl}
            onBack={() => setStory(null)}
          />
        ) : (
          <CharacterSelectScreen
            onStoryReady={(result, backendUrl) => {
              setStoryBackendUrl(backendUrl);
              setStory(result);
            }}
          />
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0f1f16',
  },
});
