/**
 * Formatting utilities for dates, numbers, and Marathi strings.
 */

export const formatDate = (dateString?: string): string => {
  if (!dateString) return '-';
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export const getLanguageBadge = (langCode?: string | null): { name: string; native: string } => {
  switch (langCode?.toLowerCase()) {
    case 'mr':
      return { name: 'Marathi', native: 'मराठी' };
    case 'hi':
      return { name: 'Hindi', native: 'हिंदी' };
    case 'en':
      return { name: 'English', native: 'English' };
    default:
      return { name: 'Marathi', native: 'मराठी' };
  }
};
