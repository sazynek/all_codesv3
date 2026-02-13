import { type ReactNode } from 'react';

interface GridProps {
    children: ReactNode;
    columns?: {
        sm?: number;
        md?: number;
        lg?: number;
        xl?: number;
    };
    gap?: number;
    className?: string;
    justify?: 'start' | 'center' | 'end' | 'between' | 'around';
    items?: 'start' | 'center' | 'end' | 'stretch';
}

export function Grid({
    children,
    columns = { sm: 1, md: 2, lg: 3, xl: 4 },
    gap = 6,
    className = '',
    justify = 'center',
    items = 'center',
}: GridProps) {
    const gridClasses = [
        'grid',
        `grid-cols-${columns.sm || 1}`,
        `md:grid-cols-${columns.md || 2}`,
        `lg:grid-cols-${columns.lg || 3}`,
        `xl:grid-cols-${columns.xl || 4}`,
        `gap-${gap}`,
        `justify-${justify}`,
        `items-${items}`,
        className,
    ].join(' ');

    return <div className={gridClasses}>{children}</div>;
}

// Вариант для списка (ul)
interface GridListProps extends GridProps {
    as?: 'ul' | 'div';
}

export function GridList({
    children,
    as: Component = 'ul',
    columns = { sm: 1, md: 2, lg: 3, xl: 4 },
    gap = 6,
    className = '',
    justify = 'center',
    items = 'center',
}: GridListProps) {
    const gridClasses = [
        'grid',
        `grid-cols-${columns.sm || 1}`,
        `md:grid-cols-${columns.md || 2}`,
        `lg:grid-cols-${columns.lg || 3}`,
        `xl:grid-cols-${columns.xl || 4}`,
        `gap-${gap}`,
        `justify-${justify}`,
        `items-${items}`,
        className,
    ].join(' ');

    return <Component className={gridClasses}>{children}</Component>;
}
