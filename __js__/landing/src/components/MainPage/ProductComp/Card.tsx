import { Link } from '@tanstack/react-router';
import type { ProductCardProps } from '../../../types';

// Компонент карточки товара
export const Card = ({ product }: ProductCardProps) => {
    const domain = 'https://www.немецкаяобувь.com';

    // Функция для получения активных бейджей
    const getActiveBadges = () => {
        const badges = [];
        if (product.badges.is_new.state) {
            badges.push(product.badges.is_new.value);
        }
        if (product.badges.hit.state) {
            badges.push(product.badges.hit.value);
        }
        if (product.is_discount.active) {
            badges.push(`-${product.is_discount.value}%`);
        }
        return badges;
    };

    const activeBadges = getActiveBadges();

    return (
        <div className='products__item bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-300 flex justify-center'>
            <Link
                to={`${product.url}`}
                className='products__link p-4 block'
                title={product.title}
            >
                {/* Изображение товара */}
                <div className='products__image relative mb-4'>
                    <img
                        src={`${domain}${product.image}`}
                        alt={product.alt}
                        className='w-[210px] h-auto object-cover rounded'
                    />

                    {/* Бейджи */}
                    {activeBadges.length > 0 && (
                        <div className='wobblers absolute top-2 left-2'>
                            <ul className='wobblers__list flex flex-wrap gap-1'>
                                {activeBadges.map((badge, index) => (
                                    <li
                                        key={index}
                                        className={`wobblers__item text-white text-xs px-2 py-1 rounded ${
                                            badge === 'NEW'
                                                ? 'bg-green-500'
                                                : badge === 'HIT'
                                                  ? 'bg-orange-500'
                                                  : 'bg-red-500'
                                        }`}
                                    >
                                        <span>{badge}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Кнопка избранного */}
                    <div className='products__to-favourites absolute top-2 right-2'>
                        <button
                            className='to-favourites__btn w-8 h-8 bg-white rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors shadow-sm'
                            title='Добавить товар в избранное'
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                // Здесь будет логика добавления в избранное
                                console.log(
                                    'Добавить в избранное:',
                                    product.id,
                                );
                            }}
                        >
                            ♡
                        </button>
                    </div>
                </div>

                {/* Название товара */}
                <span className='products__name block text-sm font-medium text-gray-800 mb-3 line-clamp-2'>
                    {product.title}
                </span>

                {/* Информация о товаре */}
                <div className='products__info mb-2 space-y-1'>
                    <div className='flex items-center gap-2 text-xs text-gray-600'>
                        <span className='font-medium'>Бренд:</span>
                        <span>{product.brand}</span>
                    </div>
                    <div className='flex items-center gap-2 text-xs text-gray-600'>
                        <span className='font-medium'>Цвет:</span>
                        <span>
                            {product.color.is_one
                                ? product.color.value[0]
                                : `${product.color.value.length} цветов`}
                        </span>
                    </div>
                    <div className='flex items-center gap-2 text-xs text-gray-600'>
                        <span className='font-medium'>Размеры:</span>
                        <span>
                            {product.sizes.length > 3
                                ? `${product.sizes[0]}-${product.sizes[product.sizes.length - 1]}`
                                : product.sizes.join(', ')}
                        </span>
                    </div>
                </div>

                {/* Цена */}
                <div className='products__price price-products'>
                    {product.price.old && (
                        <span className='price-products__old text-gray-400 line-through text-sm mr-2'>
                            {product.price.old}
                        </span>
                    )}
                    <span className='price-products__current text-lg font-bold text-gray-900'>
                        {product.price.current}
                    </span>
                </div>
            </Link>
        </div>
    );
};
