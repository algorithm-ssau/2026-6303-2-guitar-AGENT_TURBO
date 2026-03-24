import React from 'react';
import { render, screen } from '@testing-library/react';
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

    it('renders title and price correctly', () => {
        render(<GuitarCard result={mockResult} />);
        expect(screen.getByText('Fender Stratocaster')).toBeInTheDocument();
        expect(screen.getByText('1500 USD')).toBeInTheDocument();
    });

    it('renders link with target="_blank"', () => {
        render(<GuitarCard result={mockResult} />);
        const link = screen.getByRole('link', { name: /смотреть/i });
        expect(link).toHaveAttribute('href', 'https://reverb.com/item/123');
        expect(link).toHaveAttribute('target', '_blank');
    });
});
