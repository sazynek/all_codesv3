import { Link } from '@tanstack/react-router';
import { BsWrenchAdjustableCircle } from 'react-icons/bs';
import { TbHomeBitcoin } from 'react-icons/tb';
import type { BreadcrumbItem } from '../../types';
import { FaHome } from 'react-icons/fa';

interface BreadcrumbsProps {
    items?: BreadcrumbItem[];
    className?: string;
    separator?: 'slash' | 'chevron' | 'arrow' | '>';
    homeIcon?: boolean;
    variant?: 'default' | 'minimal' | 'withBackground';
    subcategories_need?: boolean;
}

export function Breadcrumbs({
    items = [
        { label: 'Главная', href: '/' },
        { label: 'Категории', href: '/category' },
    ],
    className = '',
    separator = '>',
    homeIcon = true,
    variant = 'default',
    subcategories_need = true,
}: BreadcrumbsProps) {
    const variants = {
        default: 'py-4',
        minimal: 'py-2',
        withBackground: 'bg-gray-50 rounded-lg px-4 py-3 border',
    };

    const separators = {
        slash: <span className='mx-2 text-gray-400'>/</span>,
        chevron: (
            <BsWrenchAdjustableCircle className='w-3 h-3 mx-2 text-gray-400' />
        ),
        arrow: <span className='mx-2 text-gray-400'>→</span>,
        '>': <span className='mx-2 text-gray-400'>{'>'}</span>,
    };

    // Автоматически помечаем последний элемент как текущий, если не указано явно
    const enhancedItems = items.map((item, index) => {
        const isLastItem = index === items.length - 1;
        const enhancedItem = { ...item };

        if (
            index === 0 &&
            homeIcon &&
            item.label.toUpperCase() === 'ГЛАВНАЯ' &&
            !item.icon
        ) {
            enhancedItem.icon = <FaHome className='w-4 h-4' />;
        }

        // Если isCurrent не задан явно и это последний элемент - помечаем как текущий
        if (isLastItem && enhancedItem.isCurrent === undefined) {
            enhancedItem.isCurrent = false;
        }

        return enhancedItem;
    });

    const currentItem = enhancedItems[enhancedItems.length - 1];
    console.log(`current_item = ${currentItem.title}`);

    const currentTitle = currentItem?.label || '';

    // Конвертируем Record<string, BreadcrumbItem> в массив для отображения
    const subcategories = currentItem?.subcategories
        ? Object.values(currentItem.subcategories).map((item) => ({
              label: item.label,
              href: item.href || '',
              special: item.special,
          }))
        : [];

    return (
        <div className={`breadcrumbs-wrapper ${className}`}>
            <nav className={`breadcrumbs ${variants[variant]}`}>
                <div className='breadcrumbs__inner-wrapper'>
                    <ul className='breadcrumbs__list flex items-center space-x-0 text-sm'>
                        {enhancedItems.map((item, index) => (
                            <li
                                key={index}
                                className='breadcrumbs__item flex items-center'
                            >
                                {/* Если это текущая страница - показываем как текст */}
                                {item.isCurrent ? (
                                    <span
                                        title={item.title || item.label}
                                        className='breadcrumbs__current flex items-center space-x-1 text-gray-900 font-medium cursor-default'
                                    >
                                        {item.icon && (
                                            <span className='shrink-0'>
                                                {item.icon}
                                            </span>
                                        )}
                                        <span>{item.label}</span>
                                    </span>
                                ) : (
                                    // Если не текущая - показываем как ссылку
                                    <Link
                                        to={item.href || '#'}
                                        title={item.title || item.label}
                                        className='breadcrumbs__link flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors duration-200'
                                        onClick={(e) => {
                                            // Если href не указан, предотвращаем переход
                                            if (!item.href) {
                                                e.preventDefault();
                                            }
                                        }}
                                    >
                                        {item.icon && (
                                            <span className='shrink-0'>
                                                {item.icon}
                                            </span>
                                        )}
                                        <span>{item.label}</span>
                                    </Link>
                                )}

                                {index < enhancedItems.length - 1 && (
                                    <span className='breadcrumbs__separator'>
                                        {separators[separator]}
                                    </span>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            </nav>

            {/* Заголовок текущей категории */}
            <div className='text--introduction mb-6 pt-4 text-start'>
                <h1 className='text-4xl font-bold text-gray-900'>
                    {currentTitle}
                </h1>
            </div>

            {/* Подкатегории текущего уровня */}
            {subcategories.length > 0 && subcategories_need && (
                <div className='inner-menu mb-8'>
                    <ul className='inner-menu__list flex flex-wrap gap-2'>
                        {subcategories.map((subcategory, index) => (
                            <li key={index} className='inner-menu__item'>
                                <Link
                                    to={subcategory.href}
                                    className={`inner-menu__link inline-block px-4 py-2 rounded-lg border transition-colors duration-200 ${
                                        subcategory.special
                                            ? 'bg-yellow-100 border-yellow-300 text-yellow-800 hover:bg-yellow-200'
                                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                                    }`}
                                >
                                    {subcategory.label}
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
