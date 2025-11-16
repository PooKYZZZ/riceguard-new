// Central place to configure API base URL for mobile
// Tip: On Android emulator use http://10.0.2.2:8000, on iOS simulator http://127.0.0.1:8000
// For real devices, use your computer's LAN IP, e.g., http://192.168.1.100:8000

import { Platform } from 'react-native';
import Constants from 'expo-constants';

const stripTrailingSlash = (value) => value?.replace(/\/+$/, '') ?? '';
const ensureLeadingSlash = (value) => {
  if (!value) return '';
  return value.startsWith('/') ? value : `/${value}`;
};

const ENV_EXPLICIT_BASE = process.env.EXPO_PUBLIC_API_BASE_URL
  ? stripTrailingSlash(process.env.EXPO_PUBLIC_API_BASE_URL)
  : null;
const ENV_PORT = process.env.EXPO_PUBLIC_API_PORT || '8000';
const ENV_PREFIX = stripTrailingSlash(ensureLeadingSlash(process.env.EXPO_PUBLIC_API_PREFIX || '/api/v1')) || '/api/v1';

const hostUri = Constants?.expoConfig?.hostUri || Constants?.manifest2?.extra?.expoClient?.hostUri || '';
let derivedLanOrigin = null;
if (hostUri) {
  const host = hostUri.split(':')[0];
  if (host && /^\d+\.\d+\.\d+\.\d+$/.test(host)) {
    derivedLanOrigin = `http://${host}:${ENV_PORT}`;
  }
}

const defaultHost = Platform.OS === 'android' ? '10.0.2.2' : '127.0.0.1';
const defaultOrigin = `http://${defaultHost}:${ENV_PORT}`;

let API_ORIGIN = stripTrailingSlash(derivedLanOrigin || defaultOrigin);
let API_BASE_URL = `${API_ORIGIN}${ENV_PREFIX}`;

if (ENV_EXPLICIT_BASE) {
    API_BASE_URL = stripTrailingSlash(ENV_EXPLICIT_BASE);
    try {
      const parsed = new URL(API_BASE_URL);
      API_ORIGIN = stripTrailingSlash(`${parsed.protocol}//${parsed.host}`);
    } catch (err) {
      API_ORIGIN = API_BASE_URL;
    }
}

export { API_BASE_URL, API_ORIGIN };
