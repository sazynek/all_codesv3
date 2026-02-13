import React from 'react';
import * as Accordion from '@radix-ui/react-accordion';

import { Range } from './Range'; // Импортируем компонент Range
import type { FilterParams } from '../../../../types';
import { IoChevronDownCircleOutline } from 'react-icons/io5';

interface FilterSectionAccordionProps {
    section: any;
    onOptionChange: (
        sectionId: string,
        optionId: string,
        value: boolean | number,
    ) => void;
    currentFilters: FilterParams;
}

export const FilterSectionAccordion: React.FC<FilterSectionAccordionProps> = ({
    section,
    onOptionChange,
    currentFilters,
}) => {
    // Диапазон цен на основе реальных данных из базы
    const priceRange = {
        min: 0, // Минимальная цена из базы данных
        max: 50000, // Максимальная цена из базы данных
    };

    const handlePriceChange = (min: number, max: number) => {
        onOptionChange('price', 'minPrice', min);
        onOptionChange('price', 'maxPrice', max);
    };

    return (
        <Accordion.Item value={section.id} className='border-b border-gray-200'>
            <Accordion.Header className='w-full'>
                <Accordion.Trigger className='flex justify-between items-center w-full py-4 px-4 text-left hover:bg-gray-50 transition-colors'>
                    <span className='font-medium text-gray-900'>
                        {section.title}
                    </span>
                    <IoChevronDownCircleOutline className='transition-transform duration-200 accordion-trigger' />
                </Accordion.Trigger>
            </Accordion.Header>

            <Accordion.Content className='accordion-content px-4 pb-4'>
                {section.id === 'price' ? (
                    <div className='space-y-6'>
                        {/* Ползунок цены */}
                        <div className='pt-2'>
                            <Range
                                min={priceRange.min}
                                max={priceRange.max}
                                currentMin={
                                    currentFilters.minPrice || priceRange.min
                                }
                                currentMax={
                                    currentFilters.maxPrice || priceRange.max
                                }
                                onChange={handlePriceChange}
                            />
                        </div>

                        {/* Чекбокс "Только товары со скидкой" */}
                        <div className='flex items-center space-x-3 pt-2 border-t border-gray-100'>
                            <input
                                type='checkbox'
                                id='on_sale'
                                checked={!!currentFilters.onSale}
                                onChange={(e) =>
                                    onOptionChange(
                                        'price',
                                        'on_sale',
                                        e.target.checked,
                                    )
                                }
                                className='w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
                            />
                            <label
                                htmlFor='on_sale'
                                className='text-sm text-gray-700 cursor-pointer'
                            >
                                Только товары со скидкой
                            </label>
                        </div>
                    </div>
                ) : (
                    // @ts-ignore
                    // Остальные секции фильтров
                    <div className='grid gap-2 py-1'>
                        {section.options.map(
                            (
                                // @ts-ignore
                                option,
                            ) => (
                                <div
                                    key={option.id}
                                    className='flex items-center space-x-3'
                                >
                                    <input
                                        type='checkbox'
                                        id={option.id}
                                        checked={
                                            section.id === 'size'
                                                ? currentFilters.sizes?.includes(
                                                      option.id,
                                                  ) || false
                                                : section.id === 'color'
                                                  ? currentFilters.colors?.includes(
                                                        option.id,
                                                    ) || false
                                                  : section.id === 'brand'
                                                    ? currentFilters.brands?.includes(
                                                          option.id,
                                                      ) || false
                                                    : section.id ===
                                                            'special' &&
                                                        option.id === 'on_sale'
                                                      ? !!currentFilters.onSale
                                                      : section.id ===
                                                              'special' &&
                                                          option.id === 'is_new'
                                                        ? !!currentFilters.isNew
                                                        : section.id ===
                                                                'special' &&
                                                            option.id ===
                                                                'is_hit'
                                                          ? !!currentFilters.isHit
                                                          : false
                                        }
                                        onChange={(e) =>
                                            onOptionChange(
                                                section.id,
                                                option.id,
                                                e.target.checked,
                                            )
                                        }
                                        className='w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
                                    />
                                    <label
                                        htmlFor={option.id}
                                        className='text-sm text-gray-700 cursor-pointer'
                                    >
                                        {option.label}
                                    </label>
                                </div>
                            ),
                        )}
                    </div>
                )}
            </Accordion.Content>
        </Accordion.Item>
    );
};
