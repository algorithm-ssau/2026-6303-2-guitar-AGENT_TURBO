import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { GuitarCard } from '../components/GuitarCard';

describe('GuitarCard component', () => {
    const mockResult = {
        title: 'Fender Stratocaster',
        price: 1500,
        currency: 'USD',
        listingUrl: 'https://reverb.com/item/123',
        imageUrl: 'https://url.to/cat.jpg',
    };

    it('renders title and formatted price', () => {
        render(<GuitarCard result={mockResult} />);
        expect(screen.getByText('Fender Stratocaster')).toBeInTheDocument();
        // Цена форматируется как "$1500" вместо "1500 USD"
        expect(screen.getByText('$1500')).toBeInTheDocument();
    });

    it('renders as a link with target="_blank"', () => {
        render(<GuitarCard result={mockResult} />);
        const card = screen.getByRole('link');
        expect(card).toHaveAttribute('href', 'https://reverb.com/item/123');
        expect(card).toHaveAttribute('target', '_blank');
        expect(card).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders placeholder when imageUrl is missing', () => {
        const resultWithoutImage = { ...mockResult, imageUrl: undefined };
        render(<GuitarCard result={resultWithoutImage} />);

        expect(screen.getByText('PHOTO')).toBeInTheDocument();
    });

    it('renders placeholder on image load error', () => {
        const { container } = render(<GuitarCard result={mockResult} />);

        // Находим изображение и симулируем ошибку загрузки
        const img = container.querySelector('img');
        expect(img).toBeInTheDocument();

        // Симулируем onError
        fireEvent.error(img!);

        expect(screen.getByText('PHOTO')).toBeInTheDocument();
    });

    it('displays non-USD currency in original format', () => {
        const resultWithEur = {
            ...mockResult,
            price: 800,
            currency: 'EUR',
        };
        render(<GuitarCard result={resultWithEur} />);

        // Невалютная цена отображается как "800 EUR"
        expect(screen.getByText('800 EUR')).toBeInTheDocument();
    });

    it('renders image with correct attributes', () => {
        const { container } = render(<GuitarCard result={mockResult} />);
        const img = container.querySelector('img');

        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute('src', 'https://url.to/cat.jpg');
        expect(img).toHaveAttribute('alt', 'Fender Stratocaster');
    });

    it('does not render price when price is undefined', () => {
        const resultWithoutPrice = { ...mockResult, price: undefined };
        const { container } = render(<GuitarCard result={resultWithoutPrice} />);

        // Цена не отображается — проверяем что нет элементов с ценой
        const priceElements = container.querySelectorAll('[style*="fontWeight"]');
        // Компонент не рендерит цену когда price === undefined
        expect(container.innerHTML).not.toContain('$');
        expect(container.innerHTML).not.toContain('USD');
    });
});
