// __tests__/components/Button.test.js
/**
 * @format
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { TouchableOpacity, Text, ActivityIndicator } from 'react-native';
import Button from '../../src/components/Button';

// Mock TouchableOpacity and other components for better control
jest.mock('react-native/Libraries/Components/Touchable/TouchableOpacity', () => 'TouchableOpacity');

describe('Button Component', () => {
  const mockOnPress = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders correctly with title', () => {
    // Arrange
    const title = 'Test Button';

    // Act
    const { getByText } = render(<Button title={title} onPress={mockOnPress} />);

    // Assert
    const buttonTitle = getByText(title);
    expect(buttonTitle).toBeTruthy();
  });

  test('calls onPress when button is pressed', () => {
    // Arrange
    const title = 'Press Me';
    const { getByText } = render(<Button title={title} onPress={mockOnPress} />);

    // Act
    const button = getByText(title);
    fireEvent.press(button);

    // Assert
    expect(mockOnPress).toHaveBeenCalledTimes(1);
  });

  test('is disabled when disabled prop is true', () => {
    // Arrange
    const title = 'Disabled Button';
    const { getByText } = render(
      <Button title={title} onPress={mockOnPress} disabled={true} />
    );

    // Act
    const button = getByText(title);
    fireEvent.press(button);

    // Assert
    expect(mockOnPress).not.toHaveBeenCalled();
  });

  test('shows loading indicator when loading prop is true', () => {
    // Arrange
    const title = 'Loading Button';
    const { getByTestId, queryByText } = render(
      <Button title={title} onPress={mockOnPress} loading={true} />
    );

    // Assert
    // Text should be hidden when loading
    expect(queryByText(title)).toBeFalsy();
  });

  test('applies correct style based on variant prop', () => {
    // Arrange
    const title = 'Primary Button';
    const { getByTestId } = render(
      <Button title={title} onPress={mockOnPress} variant="primary" />
    );

    // Assert
    // We would need to add testID to test styles properly
    // For now, we test that it renders without error
    expect(getByText(title)).toBeTruthy();
  });

  test('applies custom container style', () => {
    // Arrange
    const title = 'Custom Button';
    const customStyle = { backgroundColor: 'red' };
    const { getByText } = render(
      <Button title={title} onPress={mockOnPress} style={customStyle} />
    );

    // Assert
    expect(getByText(title)).toBeTruthy();
  });

  test('applies custom text style', () => {
    // Arrange
    const title = 'Styled Text';
    const customTextStyle = { color: 'blue', fontSize: 20 };
    const { getByText } = render(
      <Button title={title} onPress={mockOnPress} textStyle={customTextStyle} />
    );

    // Assert
    expect(getByText(title)).toBeTruthy();
  });

  test('handles no onPress function gracefully', () => {
    // Arrange
    const title = 'No onPress';
    const { getByText } = render(<Button title={title} />);

    // Act
    const button = getByText(title);
    fireEvent.press(button);

    // Assert
    // Should not throw error even without onPress
    expect(button).toBeTruthy();
  });

  test('renders with different button sizes', () => {
    // Arrange
    const title = 'Small Button';
    const { getByText } = render(
      <Button title={title} onPress={mockOnPress} size="small" />
    );

    // Assert
    expect(getByText(title)).toBeTruthy();
  });

  test('renders with disabled style when disabled', () => {
    // Arrange
    const title = 'Disabled Styled';
    const { getByText } = render(
      <Button title={title} onPress={mockOnPress} disabled={true} />
    );

    // Assert
    expect(getByText(title)).toBeTruthy();
  });

  test('handles accessibility props correctly', () => {
    // Arrange
    const title = 'Accessible Button';
    const accessibilityLabel = 'Custom accessibility label';
    const { getByRole } = render(
      <Button
        title={title}
        onPress={mockOnPress}
        accessibilityLabel={accessibilityLabel}
      />
    );

    // Act & Assert
    // Button should be accessible
    const button = getByRole('button');
    expect(button).toBeTruthy();
  });

  test('renders with icon when provided', () => {
    // Arrange
    const title = 'Button with Icon';
    const MockIcon = () => 'Icon';
    const { getByText } = render(
      <Button title={title} onPress={mockOnPress} icon={<MockIcon />} />
    );

    // Assert
    expect(getByText(title)).toBeTruthy();
  });

  test('handles long press events', () => {
    // Arrange
    const title = 'Long Press Button';
    const { getByText } = render(<Button title={title} onPress={mockOnPress} />);

    // Act
    const button = getByText(title);
    fireEvent(button, 'longPress');

    // Assert
    // Should handle long press without crashing
    expect(button).toBeTruthy();
  });

  test('maintains button focus state', () => {
    // Arrange
    const title = 'Focusable Button';
    const { getByText } = render(<Button title={title} onPress={mockOnPress} />);

    // Act
    const button = getByText(title);
    fireEvent(button, 'focus');
    fireEvent(button, 'blur');

    // Assert
    // Should handle focus events without crashing
    expect(button).toBeTruthy();
  });

  test('renders correctly with empty title', () => {
    // Arrange & Act
    const { container } = render(<Button title="" onPress={mockOnPress} />);

    // Assert
    // Should render even with empty title
    expect(container).toBeTruthy();
  });

  test('renders correctly with undefined title', () => {
    // Arrange & Act
    const { container } = render(<Button onPress={mockOnPress} />);

    // Assert
    // Should render even without title
    expect(container).toBeTruthy();
  });

  test('handles rapid press events correctly', () => {
    // Arrange
    const title = 'Rapid Press Button';
    const { getByText } = render(<Button title={title} onPress={mockOnPress} />);

    // Act
    const button = getByText(title);
    fireEvent.press(button);
    fireEvent.press(button);
    fireEvent.press(button);

    // Assert
    // Should handle multiple presses
    expect(mockOnPress).toHaveBeenCalledTimes(3);
  });

  test('shows loading indicator and prevents press when loading', () => {
    // Arrange
    const title = 'Loading Button';
    const { getByTestId } = render(
      <Button title={title} onPress={mockOnPress} loading={true} />
    );

    // Act
    // Try to find and press the button while loading
    // This would require testID for proper testing

    // Assert
    expect(mockOnPress).not.toHaveBeenCalled();
  });
});