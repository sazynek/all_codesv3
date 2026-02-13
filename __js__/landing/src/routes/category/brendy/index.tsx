import { createFileRoute, Link } from '@tanstack/react-router';
import { Breadcrumbs } from '../../../components/ui/Breadcrumbs';
import { getBrandsData } from '../../../data';
import type { BrandItem } from '../../../types';

export const Route = createFileRoute('/category/brendy/')({
    component: BrandsPage,
});

export function BrandsPage() {
    const { brands, breadcrumbs } = getBrandsData();

    // Разбиваем на группы по 6 элементов для 6 колонок с правильной типизацией
    const columns: BrandItem[][] = [[], [], [], [], [], []];

    brands.forEach((brand: BrandItem, index: number) => {
        const columnIndex = index % 6;
        columns[columnIndex].push(brand);
    });

    return (
        <div className='container mx-auto px-4 py-8'>
            {/* Хлебные крошки */}
            <Breadcrumbs items={breadcrumbs} />

            {/* Список брендов в 6 колонках */}
            <div className='max-w-full mx-auto text-start font-bold italic'>
                <div className='inner-menu'>
                    <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6'>
                        {columns.map((column, columnIndex) => (
                            <div
                                key={columnIndex}
                                className='inner-menu__column'
                            >
                                <ul className='space-y-2'>
                                    {column.map((brand: BrandItem) => (
                                        <li
                                            key={brand.id}
                                            className='inner-menu__item'
                                        >
                                            <Link
                                                to={brand.url}
                                                className='inner-menu__link block px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded transition-all duration-200 text-sm'
                                            >
                                                {brand.name}
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
