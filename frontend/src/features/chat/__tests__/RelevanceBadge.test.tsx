import { render, screen } from '@testing-library/react';
import { RelevanceBadge } from '../components/RelevanceBadge';

test('position=1 → Лучшее совпадение', () => {
    render(<RelevanceBadge position={1} />);
    expect(screen.getByText('Лучшее совпадение')).toBeInTheDocument();
});

test('position=3 → Отличный вариант', () => {
    render(<RelevanceBadge position={3} />);
    expect(screen.getByText('Отличный вариант')).toBeInTheDocument();
});

test('position=5 → Подходит', () => {
    render(<RelevanceBadge position={5} />);
    expect(screen.getByText('Подходит')).toBeInTheDocument();
});
