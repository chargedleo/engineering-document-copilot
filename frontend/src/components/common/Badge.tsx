import React from 'react';

interface BadgeProps {
  variant?: 'info' | 'success' | 'warning' | 'danger';
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'info', children }) => {
  return <span className={`badge badge-${variant}`}>{children}</span>;
};
