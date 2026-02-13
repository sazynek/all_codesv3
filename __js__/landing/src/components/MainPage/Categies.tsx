import { Link } from '@tanstack/react-router';
import type { CategoryItem } from '../../types';

export const Categories = () => {
    const categories: CategoryItem[] = [
        {
            id: '1',
            title: 'Женская обувь',
            url: '/category/zhenskaya-obuv/',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/e50/160_180_1c864ec529fb1f49b0f3d35348fc0bcf1/0tn952vzhz25isj2ktw1juy0abq458t6.png',
            alt: 'Женская обувь',
            className: 'categories__item --womens-shoes',
            background: '#dfa49d',
        },
        {
            id: '2',
            title: 'Мужская обувь',
            url: '/category/muzhskaya-obuv/',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/280/160_160_1c864ec529fb1f49b0f3d35348fc0bcf1/lh1qkjspyu7fnql6vd8m2yxu03p0mskm.png',
            alt: 'Мужская обувь',
            className: 'categories__item --mens-footwear',
            background: '#866e74',
        },
        {
            id: '3',
            title: 'Сумки',
            url: '/category/sumki/',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/cfd/158_171_1c864ec529fb1f49b0f3d35348fc0bcf1/wmzr9sn3v2b7p1t5ww0qyf0tx1fzi3mn.png',
            alt: 'Сумки',
            className: 'categories__item--bags',
            background: '#ab8a73',
        },
        {
            id: '4',
            title: 'Сопутствующие товары',
            url: '/category/aksessuary/',
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/uf/3ca/124_135_1c864ec529fb1f49b0f3d35348fc0bcf1/bxucsndanz7sb5lqmmn74184enkvrgds.png',
            alt: 'Сопутствующие товары',
            className: 'categories__item --related-products',
            background: '#8c8483',
        },
    ];

    return (
        <div className='container'>
            <ul className='categories__list flex flex-wrap justify-between gap-7 items-center  mt-10'>
                {categories.map((category) => (
                    <Link
                        to={category.url}
                        key={category.id}
                        className={`categories__item ${category.className} flex relative rounded group overflow-hidden`}
                        style={{ background: `${category.background}` }}
                    >
                        {/* Затемнение при наведении */}
                        <div className='absolute inset-0 bg-black opacity-0 group-hover:opacity-20 transition-opacity duration-300 z-10'></div>
                        <li>
                            <div
                                className={`categories__link group 
                        items-start
                        justify-center
                        gap-10
                        flex flex-col  text-center p-6  
                        rounded-lg transition-all duration-300 
                        mr-32
                        `}
                            >
                                <div className='categories__title text-start text-xl   font-semibold mb-5 text-white transition-colors duration-200'>
                                    {category.title}
                                </div>

                                <button
                                    className={`categories__btn inline-block 
                        bg-white px-6 py-2
                         rounded-full text-sm font-medium  
                         `}
                                    style={{ color: `${category.background}` }}
                                >
                                    Смотреть
                                </button>
                            </div>
                            <div className='categories__image mb-4 absolute top-0 right-0'>
                                <img
                                    src={category.image}
                                    alt={category.alt}
                                    className='w-40 h-40 object-contain'
                                />
                            </div>
                        </li>
                    </Link>
                ))}
            </ul>
        </div>
    );
};
