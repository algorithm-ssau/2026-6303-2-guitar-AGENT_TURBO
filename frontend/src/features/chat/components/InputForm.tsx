import React, { useState, FormEvent } from 'react';

interface InputFormProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

/**
 * Компонент формы ввода сообщения
 * Поле ввода + кнопка отправки
 */
export const InputForm: React.FC<InputFormProps> = ({ onSend, disabled = false }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Отправка по Enter без Shift
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        gap: '8px',
        padding: '16px',
        backgroundColor: '#ffffff',
        borderTop: '1px solid #e9ecef',
      }}
    >
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Введите ваш запрос..."
        disabled={disabled}
        rows={1}
        style={{
          flex: 1,
          padding: '12px 16px',
          fontSize: '16px',
          border: '1px solid #ced4da',
          borderRadius: '8px',
          resize: 'none',
          outline: 'none',
          fontFamily: 'inherit',
        }}
        onFocus={(e) => {
          e.target.style.borderColor = '#007bff';
        }}
        onBlur={(e) => {
          e.target.style.borderColor = '#ced4da';
        }}
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          fontWeight: 'bold',
          color: '#ffffff',
          backgroundColor: disabled || !input.trim() ? '#6c757d' : '#007bff',
          border: 'none',
          borderRadius: '8px',
          cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s',
        }}
      >
        ➤
      </button>
    </form>
  );
};
