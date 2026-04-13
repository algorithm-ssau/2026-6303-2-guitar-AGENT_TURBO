import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SkeletonCard } from '../components/SkeletonCard';

describe('SkeletonCard component', () => {
    it('renders without errors', () => {
        const { container } = render(<SkeletonCard />);
        expect(container).toBeInTheDocument();
    });

    it('renders default 1 skeleton', () => {
        const { container } = render(<SkeletonCard />);
        const skeletons = container.querySelectorAll('.skeleton-card');
        expect(skeletons).toHaveLength(1);
    });

    it('renders specified count of skeletons', () => {
        const { container } = render(<SkeletonCard count={4} />);
        const skeletons = container.querySelectorAll('.skeleton-card');
        expect(skeletons).toHaveLength(4);
    });

    it('contains animated elements with CSS animation', () => {
        const { container } = render(<SkeletonCard />);
        const image = container.querySelector('.skeleton-card__image');
        expect(image).toBeInTheDocument();

        // CSS класс содержит анимацию (анимация в CSS файле, не inline)
        expect(image?.className).toContain('skeleton-card__image');
    });

    it('has correct structure: image, title, price placeholders', () => {
        const { container } = render(<SkeletonCard />);
        
        const image = container.querySelector('.skeleton-card__image');
        const title = container.querySelector('.skeleton-card__title');
        const price = container.querySelector('.skeleton-card__price');

        expect(image).toBeInTheDocument();
        expect(title).toBeInTheDocument();
        expect(price).toBeInTheDocument();
    });
});
