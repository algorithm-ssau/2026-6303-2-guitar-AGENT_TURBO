/**
 * Тесты для ChatDemoScenarios — проверка изолированного demo-компонента
 */
import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatDemoScenarios } from '../demo/ChatDemoScenarios';

describe('ChatDemoScenarios', () => {
  beforeEach(() => {
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('должен рендерить список сценариев', () => {
    render(<ChatDemoScenarios />);
    expect(screen.getByText('Demo сценарии')).toBeInTheDocument();
  });

  it('должен отображать минимум 6 кнопок сценариев', () => {
    render(<ChatDemoScenarios />);
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(6);
  });

  it('должен переключать активный сценарий по клику', () => {
    render(<ChatDemoScenarios />);

    const emptyBtn = screen.getByTestId('scenario-btn-emptyChat');
    const consultationBtn = screen.getByTestId('scenario-btn-consultation');

    // По умолчанию emptyChat активен (font-weight: 600), consultation — нет (400)
    expect(emptyBtn).toHaveStyle({ fontWeight: '600' });
    expect(consultationBtn).toHaveStyle({ fontWeight: '400' });

    // Кликаем на «Консультация»
    fireEvent.click(consultationBtn);

    // Теперь consultation активна
    expect(consultationBtn).toHaveStyle({ fontWeight: '600' });
    expect(emptyBtn).toHaveStyle({ fontWeight: '400' });
  });

  it('search-сценарий должен показывать минимум одну карточку гитары', () => {
    render(<ChatDemoScenarios />);

    // Переключаемся на search-сценарий
    const searchBtn = screen.getByTestId('scenario-btn-searchResults');
    fireEvent.click(searchBtn);

    // Проверяем наличие хотя бы одного title из fixtures
    expect(
      screen.getByText(/Fender Player Telecaster/i)
    ).toBeInTheDocument();
  });

  it('error-сценарий должен показывать сообщение об ошибке', () => {
    render(<ChatDemoScenarios />);

    const errorBtn = screen.getByTestId('scenario-btn-error');
    fireEvent.click(errorBtn);

    expect(screen.getByText(/Ошибка подключения к серверу/i)).toBeInTheDocument();
  });

  it('empty-chat сценарий должен показывать welcome-экран', () => {
    render(<ChatDemoScenarios />);

    const emptyBtn = screen.getByTestId('scenario-btn-emptyChat');
    fireEvent.click(emptyBtn);

    expect(screen.getByText(/Добро пожаловать в Guitar Agent/i)).toBeInTheDocument();
  });
});
