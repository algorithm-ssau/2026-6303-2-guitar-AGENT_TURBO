import React, { useState, FormEvent } from 'react';
import './InputForm.css';

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
    <form className="input-form" onSubmit={handleSubmit}>
      <textarea
        className="input-form-textarea"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Введите ваш запрос..."
        disabled={disabled}
        rows={1}
      />
      <button
        className="input-form-submit"
        type="submit"
        disabled={disabled || !input.trim()}
      >
        ➤
      </button>
    </form>
  );
};
