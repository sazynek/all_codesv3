// Filter.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import * as Accordion from '@radix-ui/react-accordion';

import { FilterSectionAccordion } from './FilterSectionAccordion';
import { BannerSlider } from '../../../ui/Banner';
import { getFilterSections } from '../../../../data';
import type { FilterParams, FilterPropsType } from '../../../../types';

type ArrayFieldKey = 'sizes' | 'colors' | 'brands';

export const Filter = ({
    className = '',
    searchParams = {},
    isBrandPage = false,
}: FilterPropsType) => {
    const navigate = useNavigate();
    const [filters, setFilters] = useState<FilterParams>({});
    const [pendingFilters, setPendingFilters] = useState<FilterParams>({});

    const allSections = getFilterSections();

    // Фильтруем секции - скрываем бренды на страницах брендов
    const filteredSections = isBrandPage
        ? allSections.filter((section) => section.id !== 'brand')
        : allSections;

    // Логика для определения открытых секций
    const getInitialOpenSections = () => {
        return filteredSections.filter((s) => s.isOpen).map((s) => s.id);
    };

    const [openSections, setOpenSections] = useState(getInitialOpenSections());

    // Синхронизируем pendingFilters с searchParams при монтировании
    useEffect(() => {
        const initialFilters: FilterParams = {
            sizes: searchParams.sizes?.split(',').filter(Boolean) || [],
            colors: searchParams.colors?.split(',').filter(Boolean) || [],
            brands: searchParams.brands?.split(',').filter(Boolean) || [],
            minPrice: searchParams.minPrice,
            maxPrice: searchParams.maxPrice,
            onSale: searchParams.onSale === 'true',
            isNew: searchParams.isNew === 'true',
            isHit: searchParams.isHit === 'true',
        };

        setFilters(initialFilters);
        setPendingFilters(initialFilters);
    }, [searchParams]);

    // Обновляем открытые секции при изменении isBrandPage
    useEffect(() => {
        setOpenSections(getInitialOpenSections());
    }, [isBrandPage]);

    const handleOptionChange = (
        sectionId: string,
        optionId: string,
        value: boolean | number,
    ) => {
        setPendingFilters((prev) => {
            const arrayFields: Record<string, ArrayFieldKey> = {
                size: 'sizes',
                color: 'colors',
                brand: 'brands',
            };

            const specialFields: Record<string, keyof FilterParams> = {
                is_new: 'isNew',
                is_hit: 'isHit',
                on_sale: 'onSale',
            };

            // Обработка цен
            if (optionId === 'minPrice' || optionId === 'maxPrice') {
                return {
                    ...prev,
                    [optionId]: value as number,
                };
            }

            if (sectionId in arrayFields) {
                const key = arrayFields[sectionId as keyof typeof arrayFields];
                const currentArray = prev[key] || [];

                if (value) {
                    // Добавляем, если еще нет
                    return {
                        ...prev,
                        [key]: [...new Set([...currentArray, optionId])],
                    };
                } else {
                    // Удаляем
                    return {
                        ...prev,
                        [key]: currentArray.filter((item) => item !== optionId),
                    };
                }
            } else if (sectionId === 'special' && optionId in specialFields) {
                const key =
                    specialFields[optionId as keyof typeof specialFields];
                return { ...prev, [key]: value };
            } else if (sectionId === 'price' && optionId === 'on_sale') {
                return { ...prev, onSale: value };
            }

            return prev;
        });
    };

    const applyFilters = (e: React.FormEvent) => {
        e.preventDefault();

        // Применяем pendingFilters к основным фильтрам
        setFilters(pendingFilters);

        const urlParams: Record<string, any> = { pag: 1 };

        // Используем pendingFilters для формирования URL параметров
        if (pendingFilters.sizes?.length)
            urlParams.sizes = pendingFilters.sizes.join(',');
        if (pendingFilters.colors?.length)
            urlParams.colors = pendingFilters.colors.join(',');
        if (pendingFilters.brands?.length)
            urlParams.brands = pendingFilters.brands.join(',');
        if (pendingFilters.minPrice)
            urlParams.minPrice = pendingFilters.minPrice;
        if (pendingFilters.maxPrice)
            urlParams.maxPrice = pendingFilters.maxPrice;
        if (pendingFilters.onSale) urlParams.onSale = 'true';
        if (pendingFilters.isNew) urlParams.isNew = 'true';
        if (pendingFilters.isHit) urlParams.isHit = 'true';

        navigate({ search: urlParams as any });
    };

    const resetFilters = () => {
        // Сбрасываем оба состояния
        const resetState: FilterParams = {
            sizes: [],
            colors: [],
            brands: [],
            minPrice: undefined,
            maxPrice: undefined,
            onSale: false,
            isNew: false,
            isHit: false,
        };

        setFilters(resetState);
        setPendingFilters(resetState);
        // @ts-ignore
        navigate({ search: { pag: 1 } });
    };

    const hasActiveFilters = Boolean(
        filters.sizes?.length ||
            filters.colors?.length ||
            filters.brands?.length ||
            filters.minPrice ||
            filters.maxPrice ||
            filters.onSale ||
            filters.isNew ||
            filters.isHit,
    );

    const hasPendingChanges =
        JSON.stringify(filters) !== JSON.stringify(pendingFilters);

    return (
        <div className={`filter w-60 ${className}`}>
            <div className='bg-white rounded-lg border border-gray-200 overflow-hidden'>
                <div className='p-4 border-b border-gray-200'>
                    <div className='flex justify-between items-center'>
                        <h3 className='font-semibold text-gray-900'>Фильтры</h3>
                        {hasActiveFilters && (
                            <button
                                type='button'
                                onClick={resetFilters}
                                className='text-sm text-blue-600 hover:text-blue-800'
                            >
                                Сбросить
                            </button>
                        )}
                    </div>
                </div>
                <form onSubmit={applyFilters}>
                    <Accordion.Root
                        type='multiple'
                        value={openSections}
                        onValueChange={
                            setOpenSections as (value: string[]) => void
                        }
                        className='w-full'
                    >
                        {filteredSections.map((section) => (
                            <FilterSectionAccordion
                                key={section.id}
                                section={section}
                                onOptionChange={handleOptionChange}
                                currentFilters={pendingFilters}
                            />
                        ))}
                    </Accordion.Root>

                    <div className='p-4 border-t border-gray-200'>
                        <button
                            type='submit'
                            disabled={!hasPendingChanges}
                            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                                hasPendingChanges
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            }`}
                        >
                            {hasPendingChanges
                                ? 'Применить фильтр'
                                : 'Фильтры применены'}
                        </button>
                    </div>
                </form>
            </div>
            <BannerSlider />
        </div>
    );
};
