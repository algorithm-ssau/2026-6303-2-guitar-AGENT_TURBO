import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MessageItem } from '../components/Message';

// Мокаем clipboard api
Object.assign(navigator, {
    clipboard: {
        writeText: vi.fn(),
    },
});

describe('Message Component', () => {
    it('рендерит Markdown-контент для consultation-сообщения', () => {
        const consultationMsg = {
            id: '1',
            role: 'agent' as const,
            content: 'Текст с **жирным** и `кодом` и списком:\n- пункт 1',
            timestamp: new Date(),
            mode: 'consultation' as const,
        };
        render(<MessageItem message={consultationMsg} />);

        // Проверка наличия тегов
        expect(screen.getByText('жирным').tagName).toBe('STRONG');
        expect(screen.getByText('кодом').tagName).toBe('CODE');
        expect(screen.getByText('пункт 1').tagName).toBe('LI');
    });

    it('кнопка копирования присутствует для consultation-сообщений и работает', () => {
        const consultationMsg = {
            id: '2',
            role: 'agent' as const,
            content: 'Тестовый ответ',
            timestamp: new Date(),
            mode: 'consultation' as const,
        };
        render(<MessageItem message={consultationMsg} />);

        const copyBtn = screen.getByText('📋 Копировать');
        expect(copyBtn).toBeInTheDocument();

        fireEvent.click(copyBtn);
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Тестовый ответ');
        expect(screen.getByText('✅ Скопировано!')).toBeInTheDocument();
    });

    it('кнопка копирования отсутствует для user-сообщений', () => {
        const userMsg = {
            id: '3',
            role: 'user' as const,
            content: 'Мой запрос',
            timestamp: new Date(),
        };
        render(<MessageItem message={userMsg} />);

        expect(screen.queryByText(/Копировать/)).not.toBeInTheDocument();
    });
});
