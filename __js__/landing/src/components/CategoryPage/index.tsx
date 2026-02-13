// src/components/CategoryPage/index.tsx
import { Link, useSearch, useNavigate } from '@tanstack/react-router';
import { Breadcrumbs } from '../ui/Breadcrumbs';

import { CategoryDynamicPage } from '../CategoryPage/DynamicCategory/CategoryDynamicPage';
import { searchProducts } from '../../data';

export function CategoryPage() {
    const search = useSearch({ from: '/category/' });
    const navigate = useNavigate();

    const hasSearchQuery = Boolean(search.q);

    // Если есть поисковый запрос, показываем результаты поиска
    if (hasSearchQuery) {
        const searchResults = searchProducts(search.q);
        const breadcrumbItems = [
            { label: 'Главная', href: '/' },
            { label: 'Категории', href: '/category' },
            {
                label: `Результаты поиска: "${search.q}"`,
                title: `Поиск: ${search.q}`,
                isCurrent: true,
            },
        ];

        return (
            <CategoryDynamicPage
                products={searchResults}
                breadcrumbItems={breadcrumbItems}
                currentPage={search.pag}
                onPageChange={(page) => {
                    // Используем navigate вместо window.history.pushState
                    navigate({
                        to: '/category',
                        search: {
                            q: search.q,
                            pag: page,
                        },
                    });
                }}
                isSearchResults={false}
                searchQuery={search.q}
                isFilter={false}
            />
        );
    }

    // Иначе показываем обычные категории
    const categories = [
        {
            id: 1,
            slug: '/zhenskaya-obuv/',
            name: 'Женская обувь',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/425/210_210_1c864ec529fb1f49b0f3d35348fc0bcf1/w2tdco5sx1fpczliwsgxoazf1cqrkhgq.png',
            alt: 'Женская обувь',
            description: 'Элегантная и комфортная женская обувь',
        },
        {
            id: 2,
            slug: '/muzhskaya-obuv/',
            name: 'Мужская обувь',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/ae6/210_210_1c864ec529fb1f49b0f3d35348fc0bcf1/pjgekysukyzdfk03xm14z1ck9sju41rc.png',
            alt: 'Мужская обувь',
            description: 'Качественная мужская обувь для любого случая',
        },
        {
            id: 3,
            slug: '/sumki/',
            name: 'Сумки',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/2ae/210_210_1c864ec529fb1f49b0f3d35348fc0bcf1/omqi8hoc8jy5383b3f0gd0y866907vup.png',
            alt: 'Сумки',
            description: 'Стильные и практичные сумки',
        },
        {
            id: 4,
            slug: '/aksessuary/',
            name: 'Сопутствующие товары',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/688/210_210_1c864ec529fb1f49b0f3d35348fc0bcf1/aai19zf0azo5p53atlk4rp6hntkk6m9g.jpg',
            alt: 'Сопутствующие товары',
            description: 'Аксессуары и сопутствующие товары',
        },
    ];

    return (
        <div className='container mx-auto px-4 py-8'>
            <Breadcrumbs homeIcon={true} />

            <main className='main'>
                {/* Сетка категорий - центрированная по всей ширине */}
                <ul className='flex gap-20 my-20 justify-center'>
                    {categories.map((category) => (
                        <li key={category.id} className='group w-80 h-auto'>
                            <Link
                                // @ts-ignore
                                to={`/category${category.slug}`}
                                params={{ _splat: category.slug }}
                                className='block w-full'
                            >
                                <div className='bg-white rounded-lg border border-gray-200 overflow-hidden transition-all duration-300 hover:shadow-md hover:border-blue-300 h-full flex flex-col'>
                                    {/* Уменьшенное изображение */}
                                    <div className='relative overflow-hidden shrink-0'>
                                        <img
                                            src={category.image}
                                            alt={category.alt}
                                            className='w-full h-32 object-cover transition-transform duration-300 group-hover:scale-105'
                                        />
                                        <div className='absolute inset-0 bg-black opacity-0 group-hover:opacity-10 transition-all duration-300' />
                                    </div>

                                    {/* Уменьшенный контент */}
                                    <div className='p-3 flex flex-col grow'>
                                        <h3 className='font-medium text-gray-900 group-hover:text-blue-600 transition-colors text-sm text-center leading-tight mb-1'>
                                            {category.name}
                                        </h3>
                                        <p className='text-gray-600 text-xs text-center line-clamp-2 mb-2'>
                                            {category.description}
                                        </p>
                                        <div className='mt-auto pt-2 border-t border-gray-100'>
                                            <span className='text-blue-600 font-medium text-xs text-center block'>
                                                Смотреть →
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        </li>
                    ))}
                </ul>
            </main>
        </div>
    );
}
