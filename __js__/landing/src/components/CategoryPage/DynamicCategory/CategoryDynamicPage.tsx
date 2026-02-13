import type { Product, BreadcrumbItem } from '../../../types';
import { Breadcrumbs } from '../../ui/Breadcrumbs';
import { Pagination as UIPagination } from '../../ui/Pagination';
import { Card } from '../../MainPage/ProductComp/Card';
import { GridList } from '../../ui/Grid';
import { useEffect, useMemo, useRef } from 'react';
import { Filter } from './Filter';
import { useNavigate } from '@tanstack/react-router';

interface CategoryDynamicPageProps {
    products: Product[];
    breadcrumbItems: BreadcrumbItem[];
    currentPage: number;
    onPageChange: (page: number) => void;
    onResetFilters?: () => void;
    isSearchResults?: boolean;
    searchQuery?: string;
    isFilter?: boolean;
    searchParams?: any;
    categoryPath?: string;
    isBrandPage?: boolean;
    brandName?: string;
}

export function CategoryDynamicPage({
    products,
    breadcrumbItems,
    currentPage,
    onPageChange,
    onResetFilters,
    isSearchResults = false,
    searchQuery = '',
    isFilter = true,
    searchParams = {},
    categoryPath = '',
    isBrandPage = false,
    brandName = '',
}: CategoryDynamicPageProps) {
    const navigate = useNavigate();
    const ITEMS_PER_PAGE = 9;
    const prevCategoryPathRef = useRef(categoryPath);
    const prevPageRef = useRef(currentPage);

    const { currentItems, totalPages } = useMemo(() => {
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIndex = startIndex + ITEMS_PER_PAGE;
        const currentItems = products.slice(startIndex, endIndex);
        const totalPages = Math.ceil(products.length / ITEMS_PER_PAGE);
        return { currentItems, totalPages };
    }, [products, currentPage, ITEMS_PER_PAGE]);

    // Функции навигации
    const handleGoBack = () => {
        navigate({ to: '..' });
    };

    const handleGoHome = () => {
        navigate({ to: '/' });
    };

    const handleGoToCategories = () => {
        // @ts-ignore
        navigate({ to: '/category' });
    };

    const handleGoToBrands = () => {
        navigate({ to: '/category/brendy' });
    };

    // Отслеживаем смену категории
    useEffect(() => {
        if (prevCategoryPathRef.current !== categoryPath) {
            prevCategoryPathRef.current = categoryPath;
            if (currentPage !== 1) {
                onPageChange(1);
            }
        }
    }, [categoryPath, currentPage, onPageChange]);

    // Прокрутка при смене страницы
    useEffect(() => {
        if (prevPageRef.current !== currentPage) {
            const scrollTimer = setTimeout(() => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth',
                });
            }, 100);
            prevPageRef.current = currentPage;
            return () => clearTimeout(scrollTimer);
        }
    }, [currentPage, currentItems]);

    // Проверка валидности текущей страницы
    useEffect(() => {
        if (currentPage > totalPages && totalPages > 0) {
            onPageChange(1);
        }
    }, [products.length, currentPage, totalPages, onPageChange]);

    const hasActiveFilters = Object.keys(searchParams).some(
        (key) => key !== 'pag' && searchParams[key] && searchParams[key] !== '',
    );

    // Генерация заголовка в зависимости от типа страницы
    const renderHeader = () => {
        if (isSearchResults) {
            return (
                <div className='mb-6'>
                    <h1 className='text-2xl lg:text-3xl font-bold text-gray-900 mb-2'>
                        Результаты поиска: "{searchQuery}"
                    </h1>
                    <p className='text-gray-600'>
                        Найдено товаров: {products.length}
                    </p>
                </div>
            );
        }

        return null;
    };

    // Рендер кнопок навигации для пустого состояния
    const renderNavigationButtons = () => {
        const buttons = [];

        // Кнопка "Вернуться назад"
        buttons.push(
            <button
                key='back'
                onClick={handleGoBack}
                className='px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium'
            >
                ← Вернуться назад
            </button>,
        );

        // Кнопка "Все категории" (кроме страницы категорий)
        if (!isBrandPage && categoryPath !== '') {
            buttons.push(
                <button
                    key='categories'
                    onClick={handleGoToCategories}
                    className='px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 font-medium'
                >
                    Все категории
                </button>,
            );
        }

        // Кнопка "Все бренды" для страниц брендов
        if (isBrandPage) {
            buttons.push(
                <button
                    key='brands'
                    onClick={handleGoToBrands}
                    className='px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors duration-200 font-medium'
                >
                    Все бренды
                </button>,
            );
        }

        // Кнопка "На главную"
        buttons.push(
            <button
                key='home'
                onClick={handleGoHome}
                className='px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 font-medium'
            >
                На главную страницу
            </button>,
        );

        return buttons;
    };

    if (products.length === 0) {
        const getEmptyStateMessage = () => {
            if (hasActiveFilters) {
                return 'По выбранным фильтрам товаров не найдено';
            }
            if (isBrandPage) {
                return `В бренде "${brandName}" пока нет товаров`;
            }
            if (isSearchResults) {
                return `По запросу "${searchQuery}" товаров не найдено`;
            }
            return 'В этой категории пока нет товаров';
        };

        return (
            <div className='container mx-auto px-4 py-8'>
                <Breadcrumbs items={breadcrumbItems} />
                <div className='text-center py-12'>
                    <h1 className='text-2xl font-bold text-gray-900 mb-4'>
                        {getEmptyStateMessage()}
                    </h1>

                    {hasActiveFilters && onResetFilters ? (
                        <div className='flex flex-col sm:flex-row gap-4 justify-center items-center'>
                            <button
                                onClick={onResetFilters}
                                className='px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors duration-200 font-medium'
                            >
                                Сбросить фильтры
                            </button>
                            <div className='flex flex-col sm:flex-row gap-2'>
                                {renderNavigationButtons()}
                            </div>
                        </div>
                    ) : (
                        <div className='flex flex-col sm:flex-row gap-4 justify-center'>
                            {renderNavigationButtons()}
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className='container mx-auto px-4 py-8'>
            <div className='flex gap-8'>
                <div className='flex-1 min-w-0'>
                    <Breadcrumbs items={breadcrumbItems} />

                    {renderHeader()}

                    <GridList columns={{ lg: 3, md: 3, sm: 2, xl: 4 }}>
                        {currentItems.map((product) => (
                            <Card key={product.id} product={product} />
                        ))}
                    </GridList>

                    <UIPagination
                        currentPage={currentPage}
                        totalPages={totalPages}
                        onPageChange={onPageChange}
                    />
                </div>
                {isFilter && (
                    <Filter
                        searchParams={searchParams}
                        isBrandPage={isBrandPage} // Передаем пропс
                    />
                )}
            </div>
        </div>
    );
}
