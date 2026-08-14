import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

const STORAGE_KEY = "jungleBookNarrator.backendUrl";

/**
 * The FastAPI backend runs on the developer's machine. Android emulators route
 * host loopback through 10.0.2.2; iOS Simulator, physical iOS/Android devices
 * on the same Wi-Fi, and the web preview all reach it through the host's
 * regular address instead.
 */
export function defaultBackendUrl(): string {
  if (Platform.OS === "android") {
    return "http://10.0.2.2:8811";
  }
  return "http://127.0.0.1:8811";
}

export async function getBackendUrl(): Promise<string> {
  const stored = await AsyncStorage.getItem(STORAGE_KEY);
  return stored && stored.trim() ? stored.trim() : defaultBackendUrl();
}

export async function setBackendUrl(url: string): Promise<void> {
  const trimmed = url.trim().replace(/\/+$/, "");
  if (trimmed) {
    await AsyncStorage.setItem(STORAGE_KEY, trimmed);
  } else {
    await AsyncStorage.removeItem(STORAGE_KEY);
  }
}
