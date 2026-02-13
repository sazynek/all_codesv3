import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { MenuItem } from '../../../types';
import { Link } from '@tanstack/react-router';

import { database, getAllBrands } from '../../../data';

export const CategoryMenu = () => {
    const [activeMenu, setActiveMenu] = useState<string | null>(null);

    // Получаем корневые категории
    const rootCategories = database.categories.filter(
        (category) => category.parent_id === null,
    );

    // Получаем все бренды из базы данных и берем только первые 8
    const allBrands = getAllBrands().slice(0, 8);

    // Преобразуем категории в формат MenuItem
    const menuItems: MenuItem[] = rootCategories.map((rootCategory) => {
        // Получаем подкатегории для каждой корневой категории
        const subcategories = database.categories.filter(
            (cat) => cat.parent_id === rootCategory.id && !cat.is_special,
        );

        return {
            id: rootCategory.id,
            title: rootCategory.name,
            url: `/category/${rootCategory.path}/`,
            submenu: subcategories.map((subCategory) => ({
                id: subCategory.id,
                title: subCategory.name,
                url: `/category/${subCategory.path}/`,
                is_special: subCategory.is_special,
            })),
        };
    });

    // Создаем пункт меню для брендов с подменю из базы данных (только 8 брендов)
    const brandsMenuItem: MenuItem = {
        id: 'brands',
        title: 'Бренды',
        url: '/category/brendy',
        submenu: allBrands.map((brand) => ({
            id: brand.id,
            title: brand.name,
            url: brand.url,
            is_special: false,
        })),
    };

    // Создаем пункт меню для акций БЕЗ подменю
    const salesMenuItem: MenuItem = {
        id: 'sales',
        title: 'Акции',
        url: '/promos',
        // submenu: undefined - не указываем, чтобы не было выпадающего меню
    };

    // Создаем пункт меню для дисконтной программы
    const discountMenuItem: MenuItem = {
        id: 'discount',
        title: 'Дисконт',
        url: '/discount',
        submenu: [
            {
                id: 'discount-1',
                title: '💳 Получить карту',
                url: '/discount/get-card',
                is_special: false,
            },
            {
                id: 'discount-2',
                title: '⭐ Условия программы',
                url: '/discount/terms',
                is_special: false,
            },
            {
                id: 'discount-3',
                title: '💰 Мои бонусы',
                url: '/discount/my-bonuses',
                is_special: false,
            },
            {
                id: 'discount-4',
                title: '🎁 Спецпредложения',
                url: '/discount/special-offers',
                is_special: false,
            },
        ],
    };

    // Объединяем все пункты меню
    const allMenuItems = [
        ...menuItems,
        brandsMenuItem,
        salesMenuItem,
        discountMenuItem,
    ];

    // Функция для расчета количества колонок
    const getColumnsCount = (itemsCount: number) => {
        if (itemsCount <= 7) return 1;
        if (itemsCount <= 14) return 2;
        if (itemsCount <= 21) return 3;
        return 4;
    };

    // Функция для распределения элементов по колонкам
    const distributeItems = (items: any[], columns: number) => {
        const itemsPerColumn = Math.ceil(items.length / columns);
        const result = [];

        for (let i = 0; i < columns; i++) {
            result.push(
                items.slice(i * itemsPerColumn, (i + 1) * itemsPerColumn),
            );
        }

        return result;
    };

    return (
        <div className='flex w-full justify-between pt-5 relative'>
            {allMenuItems.map((item) => {
                const columnsCount = getColumnsCount(item.submenu?.length || 0);
                const distributedItems = item.submenu
                    ? distributeItems(item.submenu, columnsCount)
                    : [];

                return (
                    <div
                        key={item.id}
                        className='relative'
                        onMouseEnter={() => setActiveMenu(item.id)}
                        onMouseLeave={() => setActiveMenu(null)}
                    >
                        <Link
                            to={item.url}
                            className='text-gray-800 hover:text-[#b35424] transition-colors duration-200 py-3 px-4 rounded-md hover:bg-orange-50 text-base font-bold uppercase tracking-wide group'
                        >
                            {item.title}
                            <div className='absolute bottom-0 left-1/2 w-0 h-0.5 bg-[#b35424] transition-all duration-300 group-hover:w-4/5 group-hover:left-1/10' />
                        </Link>

                        <AnimatePresence>
                            {activeMenu === item.id &&
                                item.submenu &&
                                item.submenu.length > 0 && (
                                    <motion.div
                                        initial={{
                                            opacity: 0,
                                            y: -15,
                                            scale: 0.95,
                                        }}
                                        animate={{
                                            opacity: 1,
                                            y: 0,
                                            scale: 1,
                                        }}
                                        transition={{
                                            type: 'spring',
                                            stiffness: 600,
                                            damping: 35,
                                            duration: 0.15,
                                        }}
                                        exit={{
                                            opacity: 0,
                                            transition: { duration: 0.1 },
                                        }}
                                        className='absolute top-full left-0 mt-1 bg-white rounded-lg shadow-xl py-4 z-50 border border-gray-200'
                                        style={{
                                            minWidth: `${columnsCount * 120}px`,
                                            maxWidth: '900px',
                                        }}
                                    >
                                        <div className={`flex gap-8 px-6`}>
                                            {distributedItems.map(
                                                (column, columnIndex) => (
                                                    <ul
                                                        key={columnIndex}
                                                        className='flex-1 space-y-2 min-w-48'
                                                    >
                                                        {column.map(
                                                            (subItem) => (
                                                                <li
                                                                    key={
                                                                        subItem.id
                                                                    }
                                                                    className='internal-category-menu__item text-start'
                                                                >
                                                                    <Link
                                                                        to={
                                                                            subItem.url
                                                                        }
                                                                        className={`text-sm transition-colors duration-150 py-1 block border-b border-transparent hover:border-orange-200 whitespace-nowrap ${
                                                                            subItem.is_special
                                                                                ? 'text-red-600 hover:text-red-700 font-semibold'
                                                                                : 'text-gray-700 hover:text-[#b35424]'
                                                                        }`}
                                                                    >
                                                                        {
                                                                            subItem.title
                                                                        }
                                                                    </Link>
                                                                </li>
                                                            ),
                                                        )}
                                                    </ul>
                                                ),
                                            )}
                                        </div>
                                    </motion.div>
                                )}
                        </AnimatePresence>
                    </div>
                );
            })}
        </div>
    );
};
