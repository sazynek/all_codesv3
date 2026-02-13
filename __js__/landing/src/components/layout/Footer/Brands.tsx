import { Link } from '@tanstack/react-router';

interface Brand {
    id: string;
    name: string;
    url: string;
    images: {
        normal: string;
        hover?: string;
    };
    width: number;
    height: number;
}

export const Brand = () => {
    const domain = 'https://www.немецкаяобувь.com';

    const brands: Brand[] = [
        {
            id: '27',
            name: 'Ara',
            url: '/category/brendy/ara/',
            images: {
                normal: '/upload/resize_cache/iblock/dbf/108_37_1c864ec529fb1f49b0f3d35348fc0bcf1/dbf7392dbc07dd84c67253ddaca0d50f.png',
                hover: '/upload/resize_cache/iblock/83e/108_37_1c864ec529fb1f49b0f3d35348fc0bcf1/83e017654191cd082c6b5a880f081e4a.png',
            },
            width: 108,
            height: 37,
        },
        {
            id: '29',
            name: 'Caprice',
            url: '/category/brendy/caprice/',
            images: {
                normal: '/upload/resize_cache/iblock/f2c/138_34_1c864ec529fb1f49b0f3d35348fc0bcf1/f2c1d1370ac8b291c20ad10a294481bc.png',
                hover: '/upload/resize_cache/iblock/ae1/138_34_1c864ec529fb1f49b0f3d35348fc0bcf1/ae1039a1309fbbea4afe1b19f70ef870.png',
            },
            width: 138,
            height: 34,
        },
        {
            id: '32',
            name: 'Kelton',
            url: '/category/brendy/kelton/',
            images: {
                normal: '/upload/resize_cache/iblock/415/90_19_1c864ec529fb1f49b0f3d35348fc0bcf1/hugky5346y8nx22qq5zpc63ju8ltkf67.png',
                hover: '/upload/resize_cache/iblock/9e1/90_19_1c864ec529fb1f49b0f3d35348fc0bcf1/yo33mmo5naqexn9t180z2z3nio6efkk9.png',
            },
            width: 90,
            height: 19,
        },
        {
            id: '31',
            name: 'Waldläufer',
            url: '/category/brendy/waldlaufer/',
            images: {
                normal: '/upload/resize_cache/iblock/afd/138_30_1c864ec529fb1f49b0f3d35348fc0bcf1/afdc3426f97bbd0d2c32c37c07514665.png',
                hover: '/upload/resize_cache/iblock/c6d/138_30_1c864ec529fb1f49b0f3d35348fc0bcf1/c6d47a6ed9e93bd2b9e786c7fae054a4.png',
            },
            width: 138,
            height: 30,
        },
        {
            id: '33',
            name: 'Tamaris',
            url: '/category/brendy/tamaris/',
            images: {
                normal: '/upload/resize_cache/iblock/2d7/138_21_1c864ec529fb1f49b0f3d35348fc0bcf1/2d7d8d2617c967cea57184918bf29a96.png',
                hover: '/upload/resize_cache/iblock/353/138_21_1c864ec529fb1f49b0f3d35348fc0bcf1/353ee584f29838217fd06c91f57a225a.png',
            },
            width: 138,
            height: 21,
        },
        {
            id: '28',
            name: 'Shoiberg',
            url: '/category/brendy/shoiberg/',
            images: {
                normal: '/upload/resize_cache/iblock/bed/138_37_1c864ec529fb1f49b0f3d35348fc0bcf1/bed11dcab3bac4ef103893c893cc1fb7.png',
                hover: '/upload/resize_cache/iblock/d47/138_37_1c864ec529fb1f49b0f3d35348fc0bcf1/d47a3d32db7a1337ac073f73709477b8.png',
            },
            width: 138,
            height: 37,
        },
        {
            id: '30',
            name: 'Spur',
            url: '/category/brendy/spur/',
            images: {
                normal: '/upload/resize_cache/iblock/a2b/86_34_1c864ec529fb1f49b0f3d35348fc0bcf1/a2b09c3be716592787fa0e86f97b0200.png',
                hover: '/upload/resize_cache/iblock/abe/86_34_1c864ec529fb1f49b0f3d35348fc0bcf1/abe64945746097c5b14a526be52edda3.png',
            },
            width: 86,
            height: 34,
        },
    ];

    return (
        <section className='brands py-8 bg-[#eae5e1]'>
            <div className='container mx-auto px-4'>
                <div className='brands__row'>
                    <ul className='brands__list flex flex-wrap justify-between items-center gap-6 md:gap-8'>
                        {brands.map((brand) => (
                            <li key={brand.id} className='brands__item'>
                                <div className='brands__image'>
                                    <Link
                                        to={`${brand.url}`}
                                        className='block group'
                                    >
                                        <div className='relative'>
                                            {/* Основное изображение */}
                                            <img
                                                src={`${domain}${brand.images.normal}`}
                                                alt={brand.name}
                                                className='transition-opacity duration-300 group-hover:opacity-0'
                                                style={{
                                                    width: `${brand.width}px`,
                                                    height: `${brand.height}px`,
                                                }}
                                            />
                                            {/* Hover изображение (если есть) */}
                                            {brand.images.hover && (
                                                <img
                                                    src={`${domain}${brand.images.hover}`}
                                                    alt={brand.name}
                                                    className='absolute top-0 left-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100'
                                                    style={{
                                                        width: `${brand.width}px`,
                                                        height: `${brand.height}px`,
                                                    }}
                                                />
                                            )}
                                        </div>
                                    </Link>
                                </div>
                            </li>
                        ))}

                        {/* Кнопка "Все бренды" для десктопа */}
                        <li className='brands__item hidden md:block'>
                            <div className='brands__btn'>
                                <Link
                                    to={`/category/brendy`}
                                    className='btn bg-white hover:border-[#b35424]   border border-gray-300 text-[#b35424] px-8 text-center py-3 rounded-full transition-colors duration-200 text-sm font-medium'
                                >
                                    Все бренды
                                </Link>
                            </div>
                        </li>
                    </ul>

                    {/* Кнопка "Все бренды" для мобильных */}
                    <div className='brands__btn brands__btn--mobile mt-6 md:hidden text-center'>
                        <Link
                            to={`/category/brendy`}
                            className='btn bg-gray-800 hover:bg-gray-900 text-white px-6 py-3 rounded-lg transition-colors duration-200 text-sm font-medium inline-block'
                        >
                            Все бренды
                        </Link>
                    </div>
                </div>
            </div>
        </section>
    );
};
