// src/test/Button.test.js
/**
 * Comprehensive tests for Button component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '../components/button';

describe('Button Component', () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders button with text content', () => {
    // Arrange
    render(<Button>Click me</Button>);

    // Assert
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  test('renders with primary variant by default', () => {
    // Arrange
    render(<Button>Primary Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-primary');
  });

  test('renders with outline variant', () => {
    // Arrange
    render(<Button variant="outline">Outline Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-outline');
  });

  test('renders with custom className', () => {
    // Arrange
    render(<Button className="custom-class">Custom Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-primary', 'custom-class');
  });

  test('calls onClick when clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<Button onClick={mockOnClick}>Click me</Button>);

    // Act
    const button = screen.getByRole('button');
    await user.click(button);

    // Assert
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  test('does not call onClick when disabled', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <Button onClick={mockOnClick} disabled>
        Disabled Button
      </Button>
    );

    // Act
    const button = screen.getByRole('button');
    await user.click(button);

    // Assert
    expect(mockOnClick).not.toHaveBeenCalled();
    expect(button).toBeDisabled();
  });

  test('renders with disabled attribute when disabled prop is true', () => {
    // Arrange
    render(<Button disabled>Disabled Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  test('renders with type="button" by default', () => {
    // Arrange
    render(<Button>Default Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'button');
  });

  test('renders with custom type', () => {
    // Arrange
    render(<Button type="submit">Submit Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');
  });

  test('renders with id attribute when provided', () => {
    // Arrange
    render(<Button id="test-button">Test Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('id', 'test-button');
  });

  test('passes through additional props', () => {
    // Arrange
    render(
      <Button data-testid="custom-button" aria-label="Custom Label">
        Button with Props
      </Button>
    );

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('data-testid', 'custom-button');
    expect(button).toHaveAttribute('aria-label', 'Custom Label');
  });

  test('handles children as React elements', () => {
    // Arrange
    render(
      <Button>
        <span>Icon</span>
        <span>Text</span>
      </Button>
    );

    // Assert
    expect(screen.getByText('Icon')).toBeInTheDocument();
    expect(screen.getByText('Text')).toBeInTheDocument();
  });

  test('focuses correctly when tabbed to', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<Button>Focusable Button</Button>);

    // Act
    await user.tab();

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveFocus();
  });

  test('handles keyboard events', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<Button onClick={mockOnClick}>Keyboard Button</Button>);

    const button = screen.getByRole('button');
    button.focus();

    // Act
    await user.keyboard('{Enter}');

    // Assert
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  test('handles space key press', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<Button onClick={mockOnClick}>Space Button</Button>);

    const button = screen.getByRole('button');
    button.focus();

    // Act
    await user.keyboard('{ }');

    // Assert
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  test('prevents default form submission for type="button"', async () => {
    // Arrange
    const user = userEvent.setup();
    const mockPreventDefault = jest.fn();
    const mockEvent = {
      preventDefault: mockPreventDefault,
    };

    render(
      <Button type="button" onClick={mockOnClick}>
        Form Button
      </Button>
    );

    // Act
    const button = screen.getByRole('button');
    fireEvent.click(button, mockEvent);

    // Assert
    expect(mockPreventDefault).toHaveBeenCalled();
  });

  test('renders loading state when loading prop is true', () => {
    // Arrange
    render(<Button loading>Loading Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn-loading');
    expect(button).toBeDisabled();
  });

  test('does not call onClick when in loading state', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <Button onClick={mockOnClick} loading>
        Loading Button
      </Button>
    );

    // Act
    const button = screen.getByRole('button');
    await user.click(button);

    // Assert
    expect(mockOnClick).not.toHaveBeenCalled();
  });

  test('renders with small size modifier', () => {
    // Arrange
    render(<Button size="small">Small Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-primary', 'btn-small');
  });

  test('renders with large size modifier', () => {
    // Arrange
    render(<Button size="large">Large Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-primary', 'btn-large');
  });

  test('renders with block width modifier', () => {
    // Arrange
    render(<Button block>Block Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-primary', 'btn-block');
  });

  test('handles rapid clicks without errors', async () => {
    // Arrange
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<Button onClick={mockOnClick}>Rapid Click Button</Button>);

    // Act
    const button = screen.getByRole('button');
    for (let i = 0; i < 10; i++) {
      await user.click(button);
    }

    // Assert
    expect(mockOnClick).toHaveBeenCalledTimes(10);
  });

  test('supports ref forwarding', () => {
    // Arrange
    const ref = React.createRef();
    render(<Button ref={ref}>Ref Button</Button>);

    // Assert
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  test('handles being wrapped in form', () => {
    // Arrange
    render(
      <form>
        <Button type="submit">Form Button</Button>
      </form>
    );

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');
  });

  test('has proper accessibility attributes', () => {
    // Arrange
    render(
      <Button
        aria-label="Custom button label"
        aria-describedby="button-description"
        disabled
      >
        Accessible Button
      </Button>
    );

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Custom button label');
    expect(button).toHaveAttribute('aria-describedby', 'button-description');
    expect(button).toHaveAttribute('aria-disabled', 'true');
  });

  test('handles long text content', () => {
    // Arrange
    const longText = 'This is a very long button text that should wrap properly and not overflow';
    render(<Button>{longText}</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveTextContent(longText);
  });

  test('handles empty children gracefully', () => {
    // Arrange
    render(<Button></Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('');
  });

  test('handles null children gracefully', () => {
    // Arrange
    render(<Button>{null}</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('');
  });

  test('handles undefined children gracefully', () => {
    // Arrange
    render(<Button>{undefined}</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('');
  });

  test('handles complex React children', () => {
    // Arrange
    render(
      <Button>
        <div>
          <span>Complex</span>
          <strong>Content</strong>
        </div>
      </Button>
    );

    // Assert
    expect(screen.getByText('Complex')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  test('works correctly with CSS-in-JS styling', () => {
    // Arrange
    const customStyle = { backgroundColor: 'red', color: 'white' };
    render(
      <Button style={customStyle} className="custom-styled">
        Styled Button
      </Button>
    );

    // Assert
    const button = screen.getByRole('button');
    expect(button).toHaveStyle('background-color: red');
    expect(button).toHaveStyle('color: white');
    expect(button).toHaveClass('custom-styled');
  });

  test('handles onMouseEnter event', async () => {
    // Arrange
    const mockOnMouseEnter = jest.fn();
    const user = userEvent.setup();
    render(<Button onMouseEnter={mockOnMouseEnter}>Hover Button</Button>);

    // Act
    const button = screen.getByRole('button');
    await user.hover(button);

    // Assert
    expect(mockOnMouseEnter).toHaveBeenCalledTimes(1);
  });

  test('handles onMouseLeave event', async () => {
    // Arrange
    const mockOnMouseLeave = jest.fn();
    const user = userEvent.setup();
    render(<Button onMouseLeave={mockOnMouseLeave}>Hover Button</Button>);

    // Act
    const button = screen.getByRole('button');
    await user.hover(button);
    await user.unhover(button);

    // Assert
    expect(mockOnMouseLeave).toHaveBeenCalledTimes(1);
  });

  test('has correct role for accessibility', () => {
    // Arrange
    render(<Button>Role Test Button</Button>);

    // Assert
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });
});