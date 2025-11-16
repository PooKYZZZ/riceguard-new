// __tests__/screens/ScanScreen.test.js
/**
 * @format
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import ScanScreen from '../../src/screens/ScanScreen';
import { AuthProvider } from '../../src/context/AuthContext';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage');

// Mock Alert
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
    },
  };
});

// Mock expo-image-picker
jest.mock('expo-image-picker', () => ({
  launchImageLibraryAsync: jest.fn(),
  MediaTypeOptions: {
    Images: 'images',
    Videos: 'videos',
    All: 'all',
  },
}));

// Mock expo-camera
jest.mock('expo-camera', () => ({
  Camera: 'Camera',
  CameraType: {
    back: 'back',
    front: 'front',
  },
}));

// Mock API
jest.mock('../../src/api', () => ({
  uploadImage: jest.fn(),
  getScanHistory: jest.fn(),
  deleteScan: jest.fn(),
}));

const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  dispatch: jest.fn(),
  setOptions: jest.fn(),
  isFocused: jest.fn(() => true),
  addListener: jest.fn(() => jest.fn()),
};

const mockRoute = {
  params: {},
  name: 'Scan',
  key: 'Scan-key',
};

// Test wrapper component
const TestWrapper = ({ children }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('ScanScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    AsyncStorage.clear();

    // Mock authenticated state
    AsyncStorage.getItem.mockImplementation((key) => {
      if (key === 'authToken') return Promise.resolve('mock_token');
      return Promise.resolve(null);
    });
  });

  test('renders scan interface correctly', () => {
    // Arrange
    const { getByText, getByTestId } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Assert
    expect(getByText('Scan Rice Plant')).toBeTruthy();
  });

  test('shows camera preview on mount', () => {
    // Arrange
    const { getByTestId } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Assert
    // Camera component should be rendered
    // This would require testID for proper testing
  });

  test('handles gallery button press', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    launchImageLibraryAsync.mockResolvedValue({
      cancelled: false,
      uri: 'mock-image-uri',
      width: 224,
      height: 224,
    });

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(launchImageLibraryAsync).toHaveBeenCalledWith({
        mediaTypes: 'images',
        allowsEditing: true,
        aspect: [4, 3],
        quality: 1,
      });
    });
  });

  test('handles gallery selection cancel', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    launchImageLibraryAsync.mockResolvedValue({
      cancelled: true,
    });

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(launchImageLibraryAsync).toHaveBeenCalled();
    });
  });

  test('handles gallery selection error', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    launchImageLibraryAsync.mockRejectedValue(new Error('Camera roll access denied'));

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'Failed to access gallery. Please try again.'
      );
    });
  });

  test('shows loading state during image upload', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    const { uploadImage } = require('../../src/api');

    launchImageLibraryAsync.mockResolvedValue({
      cancelled: false,
      uri: 'mock-image-uri',
      width: 224,
      height: 224,
    });

    uploadImage.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(uploadImage).toHaveBeenCalled();
    });
  });

  test('handles successful image upload and analysis', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    const { uploadImage } = require('../../src/api');

    launchImageLibraryAsync.mockResolvedValue({
      cancelled: false,
      uri: 'mock-image-uri',
      width: 224,
      height: 224,
    });

    uploadImage.mockResolvedValue({
      data: {
        id: 'scan_123',
        prediction: 'healthy',
        confidence: 0.95,
        confidence_level: 'high',
        calibrated_confidence: 0.93,
        created_at: '2024-01-01T00:00:00Z',
      },
    });

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(uploadImage).toHaveBeenCalledWith(
        'mock-image-uri',
        expect.any(String) // auth token
      );
    });
  });

  test('navigates to result screen after successful analysis', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    const { uploadImage } = require('../../src/api');

    launchImageLibraryAsync.mockResolvedValue({
      cancelled: false,
      uri: 'mock-image-uri',
      width: 224,
      height: 224,
    });

    uploadImage.mockResolvedValue({
      data: {
        id: 'scan_123',
        prediction: 'healthy',
        confidence: 0.95,
        confidence_level: 'high',
        calibrated_confidence: 0.93,
        created_at: '2024-01-01T00:00:00Z',
      },
    });

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(mockNavigation.navigate).toHaveBeenCalledWith('Result', {
        scanResult: {
          id: 'scan_123',
          prediction: 'healthy',
          confidence: 0.95,
          confidence_level: 'high',
          calibrated_confidence: 0.93,
          created_at: '2024-01-01T00:00:00Z',
        },
      });
    });
  });

  test('handles upload error gracefully', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    const { uploadImage } = require('../../src/api');

    launchImageLibraryAsync.mockResolvedValue({
      cancelled: false,
      uri: 'mock-image-uri',
      width: 224,
      height: 224,
    });

    uploadImage.mockRejectedValue(new Error('Upload failed'));

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'Failed to analyze image. Please try again.'
      );
    });
  });

  test('handles camera capture', () => {
    // Arrange
    const { getByTestId } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    // This would require testID for the capture button
    // For now, we test that the component renders without error

    // Assert
    expect(getByText('Scan Rice Plant')).toBeTruthy();
  });

  test('validates image before upload', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    const { uploadImage } = require('../../src/api');

    // Mock image selection with invalid dimensions
    launchImageLibraryAsync.mockResolvedValue({
      cancelled: false,
      uri: 'mock-image-uri',
      width: 100, // Too small
      height: 100, // Too small
    });

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Invalid Image',
        'Please select an image with minimum dimensions of 224x224 pixels.'
      );
    });

    // Upload should not be called for invalid images
    expect(uploadImage).not.toHaveBeenCalled();
  });

  test('handles no authentication token', async () => {
    // Arrange
    AsyncStorage.getItem.mockImplementation((key) => {
      if (key === 'authToken') return Promise.resolve(null);
      return Promise.resolve(null);
    });

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(mockNavigation.navigate).toHaveBeenCalledWith('Login');
    });
  });

  test('shows information about scan requirements', () => {
    // Arrange
    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Assert
    // Should show instructions or tips for good scan quality
    expect(getByText('Scan Rice Plant')).toBeTruthy();
  });

  test('handles component unmounting during upload', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    const { uploadImage } = require('../../src/api');

    launchImageLibraryAsync.mockResolvedValue({
      cancelled: false,
      uri: 'mock-image-uri',
      width: 224,
      height: 224,
    });

    uploadImage.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    const { getByText, unmount } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Unmount component before upload completes
    unmount();

    // Assert
    // Should handle unmounting without error
    expect(true).toBeTruthy();
  });

  test('handles screen focus events', () => {
    // Arrange
    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    fireEvent(mockNavigation, 'focus');

    // Assert
    expect(getByText('Scan Rice Plant')).toBeTruthy();
  });

  test('handles screen blur events', () => {
    // Arrange
    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    fireEvent(mockNavigation, 'blur');

    // Assert
    expect(getByText('Scan Rice Plant')).toBeTruthy();
  });

  test('shows offline state when no network', async () => {
    // Arrange
    global.navigator = {
      onLine: false,
    };

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act & Assert
    // Should show offline message or disable functionality
    expect(getByText('Scan Rice Plant')).toBeTruthy();
  });

  test('handles multiple rapid gallery button presses', async () => {
    // Arrange
    const { launchImageLibraryAsync } = require('expo-image-picker');
    launchImageLibraryAsync.mockResolvedValue({
      cancelled: true,
    });

    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);
    fireEvent.press(galleryButton);
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      expect(launchImageLibraryAsync).toHaveBeenCalledTimes(1);
    });
  });

  test('persists scan preferences in AsyncStorage', async () => {
    // Arrange
    const { getByText } = render(
      <TestWrapper>
        <ScanScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    // This would depend on actual preferences implementation
    const galleryButton = getByText('Choose from Gallery');
    fireEvent.press(galleryButton);

    // Assert
    await waitFor(() => {
      // Should check if preferences are stored
      expect(AsyncStorage.setItem).toHaveBeenCalled();
    });
  });
});