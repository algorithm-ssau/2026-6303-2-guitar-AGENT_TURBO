import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GuitarCard } from '../components/GuitarCard';
import { GuitarResult } from '../types';

const mockGuitar: GuitarResult = {
    id: 'test-123',
    title: 'Gibson Les Paul',
    price: 1000,
    currency: 'USD',
    listingUrl: 'http://test.com',
};

describe('GuitarCard Feedback', () => {
    it('вызывает onFeedback с rating="up" при клике на 👍', () => {
        const handleFeedback = vi.fn(); // Используем vi.fn() вместо jest.fn() для Vitest
        render(
            <GuitarCard 
                result={mockGuitar} 
                onFeedback={handleFeedback} 
                feedbackGiven={false} 
            />
        );

        const upButton = screen.getByText('👍');
        fireEvent.click(upButton);
        
        expect(handleFeedback).toHaveBeenCalledWith('test-123', 'up');
    });

    it('вызывает onFeedback с rating="down" при клике на 👎', () => {
        const handleFeedback = vi.fn();
        render(
            <GuitarCard 
                result={mockGuitar} 
                onFeedback={handleFeedback} 
                feedbackGiven={false} 
            />
        );

        const downButton = screen.getByText('👎');
        fireEvent.click(downButton);
        
        expect(handleFeedback).toHaveBeenCalledWith('test-123', 'down');
    });

    it('блокирует кнопки, если feedbackGiven = true', () => {
        const handleFeedback = vi.fn();
        render(
            <GuitarCard 
                result={mockGuitar} 
                onFeedback={handleFeedback} 
                feedbackGiven={true} 
            />
        );

        const upButton = screen.getByText('👍');
        const downButton = screen.getByText('👎');

        expect(upButton).toBeDisabled();
        expect(downButton).toBeDisabled();
    });
});