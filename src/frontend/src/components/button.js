import React from 'react';
import './button.css';

export default function Button({ variant = 'primary', children, type = 'button', onClick, className = '', ...rest }) {
  const variantClass = variant === 'outline' ? 'btn-outline' : 'btn-primary';
  const cls = ['btn', variantClass, className].filter(Boolean).join(' ');
  return (
    <button type={type} className={cls} onClick={onClick} {...rest}>
      {children}
    </button>
  );
}
