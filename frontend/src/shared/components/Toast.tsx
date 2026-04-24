import { useEffect, type CSSProperties } from 'react';

export type ToastType = 'success' | 'error' | 'info';

type ToastProps = {
  text: string;
  type: ToastType;
  onClose: () => void;
  durationMs?: number;
};

const toneStyles: Record<ToastType, CSSProperties> = {
  success: {
    background: 'var(--success-bg)',
    borderColor: 'var(--success)',
    color: 'var(--success-text)',
  },
  error: {
    background: 'var(--danger-bg)',
    borderColor: 'var(--danger)',
    color: 'var(--danger-text)',
  },
  info: {
    background: 'var(--info-bg)',
    borderColor: 'var(--accent)',
    color: 'var(--info-text)',
  },
};

const toastStyle: CSSProperties = {
  position: 'fixed',
  right: 24,
  bottom: 24,
  zIndex: 1000,
  maxWidth: 360,
  minWidth: 220,
  padding: '12px 16px',
  border: '1px solid',
  borderRadius: 'var(--radius-sm)',
  boxShadow: 'var(--shadow)',
  fontFamily: 'var(--font-family)',
  fontSize: 14,
  lineHeight: 1.4,
};

export function Toast({ text, type, onClose, durationMs = 3000 }: ToastProps) {
  useEffect(() => {
    const timerId = window.setTimeout(onClose, durationMs);
    return () => window.clearTimeout(timerId);
  }, [durationMs, onClose]);

  return (
    <div role="status" aria-live="polite" style={{ ...toastStyle, ...toneStyles[type] }}>
      {text}
    </div>
  );
}
