import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { fonts } from '../theme/typography';

export default function Button({
  variant = 'primary',
  style,
  textStyle,
  disabled,
  children,
  ...props
}) {
  const variantStyle = variant === 'primary' ? styles.primary : styles.outline;
  const textVariantStyle = variant === 'primary' ? styles.textPrimary : styles.textOutline;
  return (
    <TouchableOpacity
      activeOpacity={0.8}
      style={[
        styles.base,
        variantStyle,
        disabled && styles.disabled,
        style,
      ]}
      disabled={disabled}
      {...props}
    >
      <Text style={[styles.text, textVariantStyle, disabled && styles.textDisabled, textStyle]}>
        {children}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 6,
  },
  primary: {
    backgroundColor: '#2563eb',
  },
  outline: {
    borderWidth: 1,
    borderColor: '#2563eb',
    backgroundColor: 'transparent',
  },
  disabled: {
    opacity: 0.6,
  },
  text: { fontSize: 16, fontFamily: fonts.semi },
  textPrimary: { color: 'white' },
  textOutline: { color: '#2563eb' },
  textDisabled: { color: '#d1d5db' },
});
