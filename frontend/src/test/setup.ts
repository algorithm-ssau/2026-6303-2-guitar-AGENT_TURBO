import '@testing-library/jest-dom';

// Мок для scrollIntoView (не реализован в jsdom)
Element.prototype.scrollIntoView = vi.fn();
