import React, { useState, useEffect } from 'react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import type { PriceRangeSliderProps } from '../../../../types';

export const Range: React.FC<PriceRangeSliderProps> = ({
    min,
    max,
    onChange,
    currentMin = min,
    currentMax = max,
}) => {
    const [values, setValues] = useState([currentMin, currentMax]);

    useEffect(() => {
        setValues([currentMin, currentMax]);
    }, [currentMin, currentMax]);

    const handleChange = (newValues: number | number[]) => {
        if (Array.isArray(newValues)) {
            setValues(newValues);
            onChange(newValues[0], newValues[1]);
        }
    };

    const handleChangeComplete = (newValues: number | number[]) => {
        if (Array.isArray(newValues)) {
            // Дополнительная логика при завершении изменения, если нужно
            console.log('Range selection completed:', newValues);
        }
    };

    return (
        <div className='price-range-slider space-y-4'>
            {/* Слайдер */}
            <div className='px-2'>
                <Slider
                    range
                    min={min}
                    max={max}
                    value={values}
                    onChange={handleChange}
                    onChangeComplete={handleChangeComplete}
                    styles={{
                        track: {
                            background: '#3b82f6',
                            height: 6,
                        },
                        // @ts-ignore
                        handles: [
                            {
                                borderColor: '#3b82f6',
                                height: 18,
                                width: 18,
                                backgroundColor: '#ffffff',
                                opacity: 1,
                            },
                            {
                                borderColor: '#3b82f6',
                                height: 18,
                                width: 18,
                                backgroundColor: '#ffffff',
                                opacity: 1,
                            },
                        ],
                        rail: {
                            background: '#d1d5db',
                            height: 6,
                        },
                    }}
                    allowCross={false}
                    pushable={true}
                    keyboard={true}
                    ariaLabelForHandle={[
                        'Минимальная цена',
                        'Максимальная цена',
                    ]}
                    ariaValueTextFormatterForHandle={[
                        (value) => `${value} рублей`,
                        (value) => `${value} рублей`,
                    ]}
                />
            </div>

            {/* Отображение значений */}
            <div className='flex justify-between items-center text-sm text-gray-600'>
                <span className='font-medium'>
                    {values[0].toLocaleString()} ₽
                </span>
                <span className='text-gray-400'>—</span>
                <span className='font-medium'>
                    {values[1].toLocaleString()} ₽
                </span>
            </div>
        </div>
    );
};
