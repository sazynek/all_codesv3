import { useState, useEffect } from 'react';
import { useCombobox } from 'downshift';
import { FaSearch, FaExclamationTriangle } from 'react-icons/fa';
import { Link, useNavigate } from '@tanstack/react-router';
import type { Product } from '../../../types';
import { filterProducts } from '../../../data'; // Импортируем новую функцию

export function Input() {
    const domain = 'https://www.немецкаяобувь.com';
    const navigate = useNavigate();

    const [inputItems, setInputItems] = useState<Product[]>([]);
    const [timeoutId, setTimeoutId] = useState<any>();
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);

    // Используем новую функцию фильтрации
    const searchProducts = (query: string): Product[] => {
        if (!query.trim()) return [];

        console.log('search: ', query);
        return filterProducts({ query }).slice(0, 5); // Берем первые 5 результатов
    };

    // Функция для очистки input и сброса состояния
    const clearSearch = () => {
        setSearchQuery('');
        setInputItems([]);
        setIsSearching(false);
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
    };

    // Функция для выполнения поиска
    const performSearch = (query: string) => {
        if (query.trim()) {
            navigate({
                to: '/category',
                search: { q: query.trim(), pag: 1 }, // pag: 1 вместо 0
            });
            closeMenu();
            clearSearch();
        }
    };

    const {
        isOpen,
        getMenuProps,
        getInputProps,
        highlightedIndex,
        getItemProps,
        closeMenu,
        reset,
    } = useCombobox({
        items: inputItems,
        onInputValueChange: ({ inputValue }) => {
            if (timeoutId) clearTimeout(timeoutId);
            setSearchQuery(inputValue || '');

            if (!inputValue || inputValue.trim().length === 0) {
                setInputItems([]);
                setIsSearching(false);
                return;
            }

            setIsSearching(true);

            const newTimeoutId = setTimeout(() => {
                const results = searchProducts(inputValue);
                setInputItems(results);
                setIsSearching(false);
            }, 300); // Уменьшил задержку для лучшего UX

            setTimeoutId(newTimeoutId);
        },
        itemToString: (item) => item?.title || '',
    });

    useEffect(() => {
        return () => {
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [timeoutId]);

    // Обработчик отправки формы
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        performSearch(searchQuery);
    };

    // Обработчик нажатия клавиш в поле ввода
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && highlightedIndex === -1) {
            e.preventDefault();
            performSearch(searchQuery);
        }
    };

    // Кастомные пропсы для input
    const customInputProps = {
        ...getInputProps(),
        onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => {
            getInputProps().onKeyDown?.(e);
            handleKeyDown(e);
        },
        value: searchQuery,
    };

    // Кастомные пропсы для элементов списка
    const customGetItemProps = ({
        item,
        index,
    }: {
        item: Product;
        index: number;
    }) => {
        const originalProps = getItemProps({ item, index });

        return {
            ...originalProps,
            onClick: (e: React.MouseEvent) => {
                clearSearch();
                originalProps.onClick?.(e);
            },
        };
    };

    // Упрощенная логика отображения
    const showResults = isOpen && inputItems.length > 0;
    const showNoResults =
        isOpen && !isSearching && searchQuery.trim() && inputItems.length === 0;
    const showLoading = isOpen && isSearching;

    return (
        <div className='relative w-full max-w-2xl'>
            <form onSubmit={handleSubmit}>
                <div className='flex items-center rounded-full border border-gray-200 bg-white overflow-hidden transition-all duration-200 hover:shadow-sm focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400'>
                    <input
                        {...customInputProps}
                        placeholder='Поиск по коду или названию товара'
                        autoComplete='off'
                        className='flex-1 min-w-0 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none bg-transparent'
                    />
                    <button
                        type='submit'
                        className='text-gray-400 hover:text-gray-600 px-3 py-2 flex items-center justify-center transition-colors duration-200 hover:bg-gray-50'
                    >
                        <FaSearch className='w-4 h-4' />
                    </button>
                </div>
            </form>

            {/* Выпадающий список */}
            {(showResults || showNoResults || showLoading) && (
                <ul
                    {...getMenuProps()}
                    className='absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto'
                >
                    {showLoading && (
                        <li className='px-4 py-4 text-center text-gray-500'>
                            <div className='flex flex-col items-center justify-center'>
                                <div className='animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-2'></div>
                                <p className='font-medium'>Поиск...</p>
                                <p className='text-sm mt-1'>
                                    Ищем товары по запросу "{searchQuery}"
                                </p>
                            </div>
                        </li>
                    )}

                    {showResults &&
                        inputItems.map((item, index) => (
                            <li
                                key={item.id}
                                {...customGetItemProps({ item, index })}
                                className={`px-4 py-3 cursor-pointer ${
                                    highlightedIndex === index
                                        ? 'bg-blue-50'
                                        : 'hover:bg-gray-50'
                                } border-b border-gray-100 last:border-b-0 transition-colors duration-150`}
                            >
                                <Link to={item.url} className='block'>
                                    <div className='flex items-center space-x-3'>
                                        <img
                                            src={`${domain}${item.image}`}
                                            alt={item.alt}
                                            className='w-10 h-10 object-cover rounded shrink-0'
                                            onError={(e) => {
                                                (
                                                    e.target as HTMLImageElement
                                                ).src =
                                                    '/images/placeholder.jpg';
                                            }}
                                        />
                                        <div className='flex-1 text-start min-w-0'>
                                            <p className='text-sm font-medium text-gray-900 truncate'>
                                                {item.title}
                                            </p>
                                            <div className='flex items-center space-x-2 mt-1'>
                                                <span className='text-sm font-semibold text-green-600'>
                                                    {item.price.current}
                                                </span>
                                                {item.price.old && (
                                                    <span className='text-sm text-gray-500 line-through'>
                                                        {item.price.old}
                                                    </span>
                                                )}
                                                {item.badges &&
                                                    item.badges.length > 0 && (
                                                        <span className='text-xs bg-red-100 text-red-800 px-1 rounded'>
                                                            {item.badges[0]}
                                                        </span>
                                                    )}
                                            </div>
                                        </div>
                                    </div>
                                </Link>
                            </li>
                        ))}

                    {showNoResults && (
                        <li className='px-4 py-6 text-center text-gray-500'>
                            <div className='flex flex-col items-center justify-center'>
                                <FaExclamationTriangle className='w-8 h-8 text-gray-400 mb-2' />
                                <p className='font-medium'>Товары не найдены</p>
                                <p className='text-sm mt-1'>
                                    По запросу "{searchQuery}" ничего не найдено
                                </p>
                                <p className='text-xs mt-2 text-gray-400'>
                                    Попробуйте изменить запрос
                                </p>
                            </div>
                        </li>
                    )}
                </ul>
            )}
        </div>
    );
}
