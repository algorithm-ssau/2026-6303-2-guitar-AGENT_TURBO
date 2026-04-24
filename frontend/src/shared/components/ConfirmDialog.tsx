import type { CSSProperties } from 'react';

type ConfirmDialogProps = {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
};

const overlayStyle: CSSProperties = {
  position: 'fixed',
  inset: 0,
  zIndex: 999,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 20,
  background: 'var(--overlay)',
};

const dialogStyle: CSSProperties = {
  width: 'min(420px, 100%)',
  padding: 20,
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  background: 'var(--bg-card)',
  color: 'var(--text-main)',
  boxShadow: 'var(--shadow)',
  fontFamily: 'var(--font-family)',
};

const titleStyle: CSSProperties = {
  margin: '0 0 8px',
  fontSize: 18,
  lineHeight: 1.3,
};

const messageStyle: CSSProperties = {
  margin: 0,
  color: 'var(--text-subtle)',
  fontSize: 14,
  lineHeight: 1.5,
};

const actionsStyle: CSSProperties = {
  display: 'flex',
  justifyContent: 'flex-end',
  gap: 10,
  marginTop: 20,
};

const buttonBaseStyle: CSSProperties = {
  minWidth: 86,
  padding: '9px 14px',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  font: 'inherit',
  cursor: 'pointer',
};

const cancelButtonStyle: CSSProperties = {
  ...buttonBaseStyle,
  background: 'var(--surface-muted)',
  color: 'var(--text-main)',
};

const confirmButtonStyle: CSSProperties = {
  ...buttonBaseStyle,
  borderColor: 'var(--accent)',
  background: 'var(--accent)',
  color: 'var(--text-inverse)',
};

export function ConfirmDialog({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div role="presentation" style={overlayStyle}>
      <div role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title" style={dialogStyle}>
        <h2 id="confirm-dialog-title" style={titleStyle}>
          {title}
        </h2>
        <p style={messageStyle}>{message}</p>
        <div style={actionsStyle}>
          <button type="button" onClick={onCancel} style={cancelButtonStyle}>
            Отмена
          </button>
          <button type="button" onClick={onConfirm} style={confirmButtonStyle}>
            Да
          </button>
        </div>
      </div>
    </div>
  );
}
