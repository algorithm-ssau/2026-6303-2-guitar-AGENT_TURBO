import React from 'react';
import { render, screen } from '@testing-library/react';
import { StatusIndicator } from '../components/StatusIndicator';

describe('StatusIndicator', () => {
  it('isLoading=true, status="Ищу на Reverb..." → текст отображается', () => {
    render(<StatusIndicator status="Ищу на Reverb..." isLoading={true} />);
    
    expect(screen.getByText(/Ищу на Reverb\.\.\./)).toBeInTheDocument();
  });

  it('isLoading=false → компонент не рендерится', () => {
    const { container } = render(<StatusIndicator status="Ищу на Reverb..." isLoading={false} />);
    
    expect(container.firstChild).toBeNull();
  });

  it('isLoading=true, status=null → "Подключение..."', () => {
    render(<StatusIndicator status={null} isLoading={true} />);
    
    expect(screen.getByText(/Подключение\.\.\./)).toBeInTheDocument();
  });

  it('отображает эмодзи робота при загрузке', () => {
    render(<StatusIndicator status="Тестовый статус" isLoading={true} />);
    
    expect(screen.getByText('🤖')).toBeInTheDocument();
  });

  it('отображает прогресс-бар при загрузке', () => {
    render(<StatusIndicator status="Тестовый статус" isLoading={true} />);
    
    // Проверяем наличие элемента с анимацией loading
    const progressBar = document.querySelector('div[style*="animation: \'loading']');
    expect(progressBar).toBeInTheDocument();
  });
});
