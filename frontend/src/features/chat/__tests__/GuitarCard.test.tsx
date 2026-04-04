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
        imageUrl: 'https://url.to/cat.jpg'
    };

    it('renders title and formatted price', () => {
        render(<GuitarCard result={mockResult} />);
        expect(screen.getByText('Fender Stratocaster')).toBeInTheDocument();
        // Цена форматируется как "$1500" вместо "1500 USD"
        expect(screen.getByText('$1500')).toBeInTheDocument();
    });

    it('renders link with target="_blank"', () => {
        render(<GuitarCard result={mockResult} />);
        const link = screen.getByRole('link', { name: /смотреть/i });
        expect(link).toHaveAttribute('href', 'https://reverb.com/item/123');
        expect(link).toHaveAttribute('target', '_blank');
    });

    it('renders placeholder when imageUrl is missing', () => {
        const resultWithoutImage = { ...mockResult, imageUrl: undefined };
        render(<GuitarCard result={resultWithoutImage} />);

        expect(screen.getByText('Нет фото')).toBeInTheDocument();
    });

    it('renders placeholder on image load error', () => {
        const { container } = render(<GuitarCard result={mockResult} />);

        // Находим изображение и симулируем ошибку загрузки
        const img = container.querySelector('img');
        expect(img).toBeInTheDocument();

        // Симулируем onError
        fireEvent.error(img!);

        expect(screen.getByText('Нет фото')).toBeInTheDocument();
    });

    it('image link has target="_blank"', () => {
        const { container } = render(<GuitarCard result={mockResult} />);

        // Находим ссылку вокруг изображения
        const img = container.querySelector('img');
        expect(img).toBeInTheDocument();

        // Ссылка-обёртка изображения должна иметь target="_blank"
        const imageLink = img?.closest('a');
        expect(imageLink).toHaveAttribute('target', '_blank');
        expect(imageLink).toHaveAttribute('href', 'https://reverb.com/item/123');
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
});
