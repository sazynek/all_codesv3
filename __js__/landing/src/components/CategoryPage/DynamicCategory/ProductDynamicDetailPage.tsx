import { useEffect, useState } from 'react';
import type { BreadcrumbItem, Product } from '../../../types';
import { Breadcrumbs } from '../../ui/Breadcrumbs';

interface ProductDetailPageProps {
    product: Product;
    breadcrumbItems: BreadcrumbItem[];
}

// Имитация данных для галереи
const productGalleryImages = [
    '/upload/resize_cache/iblock/c12/450_450_2c864ec529fb1f49b0f3d35348fc0bcf1/y065ygopbc2zmtg1f9brclw8fmhpbo0t.jpg',
    '/upload/resize_cache/iblock/eef/450_450_2c864ec529fb1f49b0f3d35348fc0bcf1/sv116gdmhr1ab2c7rhlqz2thwm5b3frl.jpg',
    '/upload/resize_cache/iblock/e44/450_450_2c864ec529fb1f49b0f3d35348fc0bcf1/i1nwzb036auorc48vaq9h9rrc7247mst.jpg',
    '/upload/resize_cache/iblock/b09/450_450_2c864ec529fb1f49b0f3d35348fc0bcf1/82zk2z8d3qwzkdrh7mxevb5s7pud5yi3.jpg',
];

// Мини-версия Card для миниатюр
const ThumbnailCard = ({
    image,
    alt,
    isActive,
    onClick,
}: {
    image: string;
    alt: string;
    isActive: boolean;
    onClick: () => void;
}) => {
    const domain = 'https://www.немецкаяобувь.com';

    return (
        <div
            className={`cursor-pointer border-2 rounded-lg transition-all ${
                isActive
                    ? 'border-blue-500 scale-105'
                    : 'border-transparent hover:border-gray-300'
            }`}
            onClick={onClick}
        >
            <img
                src={`${domain}${image}`}
                alt={alt}
                className='w-16 h-16 lg:w-20 lg:h-20 object-cover rounded'
            />
        </div>
    );
};

// Данные для таба "Наличие в магазинах"
const storeAvailabilityData = {
    sizes: [40, 41, 42, 43, 44, 45],
    stores: {
        40: [
            {
                id: 15,
                name: '«Большой Гостиный Двор», Перинная линия, 1 этаж',
                phone: '8 (812) 509-40-24',
                metro: ['Невский пр.', 'Гостиный двор'],
                badges: [],
            },
        ],
        41: [
            {
                id: 15,
                name: '«Большой Гостиный Двор», Перинная линия, 1 этаж',
                phone: '8 (812) 509-40-24',
                metro: ['Невский пр.', 'Гостиный двор'],
                badges: [],
            },
        ],
        42: [
            {
                id: 15,
                name: '«Большой Гостиный Двор», Перинная линия, 1 этаж',
                phone: '8 (812) 509-40-24',
                metro: ['Невский пр.', 'Гостиный двор'],
                badges: [],
            },
            {
                id: 77253,
                name: 'Садовая ул., д. 46',
                phone: '8 (812) 509-40-15',
                metro: ['Сенная пл.', 'Садовая', 'Спасская'],
                badges: [],
            },
        ],
        43: [
            {
                id: 15,
                name: '«Большой Гостиный Двор», Перинная линия, 1 этаж',
                phone: '8 (812) 509-40-24',
                metro: ['Невский пр.', 'Гостиный двор'],
                badges: [],
            },
        ],
        44: [
            {
                id: 15,
                name: '«Большой Гостиный Двор», Перинная линия, 1 этаж',
                phone: '8 (812) 509-40-24',
                metro: ['Невский пр.', 'Гостиный двор'],
                badges: [],
            },
        ],
        45: [
            {
                id: 15,
                name: '«Большой Гостиный Двор», Перинная линия, 1 этаж',
                phone: '8 (812) 509-40-24',
                metro: ['Невский пр.', 'Гостиный двор'],
                badges: [],
            },
        ],
    },
    allStores: [
        {
            id: 199,
            name: 'Садовая ул., д. 33',
            phone: '8 (812) 509-40-14',
            metro: ['Сенная пл.', 'Садовая', 'Спасская'],
            badges: ['discount'],
        },
        {
            id: 3030,
            name: 'г. Пушкин, Московская ул., д. 25 (вход с ул. Оранжерейная)',
            phone: '8 (812) 509-40-23',
            metro: [],
            badges: [],
        },
        {
            id: 200,
            name: 'Ленинский пр., д. 119',
            phone: '8 (812) 509-40-18',
            metro: ['Ленинский пр.'],
            badges: [],
        },
        {
            id: 16,
            name: 'Загородный пр., д. 8, салон "Gabor"',
            phone: '8 (812) 409-38-45',
            metro: ['Владимирская', 'Достоевская'],
            badges: ['gabor'],
        },
        {
            id: 3037,
            name: 'Большой пр. П. С., д. 63',
            phone: '8 (812) 509-40-13',
            metro: ['Петроградская'],
            badges: [],
        },
        {
            id: 3038,
            name: 'Комендантский пр., д. 16',
            phone: '8 (812) 509-40-17',
            metro: ['Комендантский пр.'],
            badges: [],
        },
        {
            id: 3029,
            name: 'ул. Комсомола, д. 45',
            phone: '8 (812) 509-40-19',
            metro: ['пл. Ленина'],
            badges: [],
        },
        {
            id: 3036,
            name: 'пр. Большевиков, д. 3',
            phone: '8 (812) 509-40-16',
            metro: ['пр. Большевиков'],
            badges: [],
        },
        {
            id: 3032,
            name: 'пр. Энгельса, д. 128',
            phone: '8 (812) 509-40-21',
            metro: ['Озерки', 'пр. Просвещения'],
            badges: [],
        },
        {
            id: 76858,
            name: 'Торфяная дорога, д. 7, ТРК "Гулливер", 2 корпус, 3 этаж',
            phone: '8 (812) 509-40-12',
            metro: ['Старая деревня'],
            badges: [],
        },
        {
            id: 77253,
            name: 'Садовая ул., д. 46',
            phone: '8 (812) 509-40-15',
            metro: ['Сенная пл.', 'Садовая', 'Спасская'],
            badges: [],
        },
        {
            id: 85859,
            name: 'пр. Энгельса, 154, ТРК "Гранд Каньон", 1 этаж, салон "Gabor"',
            phone: '8 (812) 409-38-58',
            metro: ['пр. Просвещения', 'Парнас'],
            badges: ['gabor'],
        },
    ],
};

export function ProductDynamicDetailPage({
    product,
    breadcrumbItems,
}: ProductDetailPageProps) {
    const domain = 'https://www.немецкаяобувь.com';
    const [selectedSize, setSelectedSize] = useState<number>(product.sizes[0]);
    const [mainImage, setMainImage] = useState<string>(productGalleryImages[0]);
    const [isInCart, setIsInCart] = useState(false);
    const [isInWishlist, setIsInWishlist] = useState(false);
    const [activeTab, setActiveTab] = useState('characteristics');
    const [availabilitySelectedSize, setAvailabilitySelectedSize] =
        useState<number>(product.sizes[0]);

    // Сбрасываем состояние при изменении продукта
    useEffect(() => {
        setMainImage(productGalleryImages[0]);
        setIsInCart(false);
        setIsInWishlist(false);
        setSelectedSize(product.sizes[0]);
        setAvailabilitySelectedSize(product.sizes[0]);
    }, [product.id]);

    // Прокрутка вверх при загрузке страницы товара
    useEffect(() => {
        const timer = setTimeout(() => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }, 100);
        return () => clearTimeout(timer);
    }, [product.id]);

    const handleAddToCart = () => {
        setIsInCart(true);
        // Здесь будет логика добавления в корзину
    };

    const handleToggleWishlist = () => {
        setIsInWishlist(!isInWishlist);
        // Здесь будет логика добавления/удаления из избранного
    };

    const handleOneClickBuy = () => {
        alert('Форма быстрого заказа будет открыта');
    };

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

    // Функция для получения цвета метро
    const getMetroColorClass = (index: number) => {
        const colors = [
            'bg-blue-100 text-blue-800',
            'bg-purple-100 text-purple-800',
            'bg-orange-100 text-orange-800',
            'bg-red-100 text-red-800',
            'bg-green-100 text-green-800',
        ];
        return colors[index % colors.length];
    };

    // Функция для получения класса бейджа
    const getBadgeClass = (badge: string) => {
        switch (badge) {
            case 'discount':
                return 'bg-yellow-100 text-yellow-800';
            case 'gabor':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    // Функция для получения текста бейджа
    const getBadgeText = (badge: string) => {
        switch (badge) {
            case 'discount':
                return 'Дисконт';
            case 'gabor':
                return 'Gabor';
            default:
                return badge;
        }
    };

    // Функция для рендеринга контента табов
    const renderTabContent = () => {
        switch (activeTab) {
            case 'characteristics':
                return (
                    <div className='space-y-8 text-left'>
                        <div className='characteristics'>
                            <div className='grid grid-cols-1 lg:grid-cols-2 gap-16'>
                                <div className='space-y-6'>
                                    <h2 className='text-xl font-bold'>
                                        Состав изделия
                                    </h2>
                                    <ul className='space-y-4'>
                                        <li className='flex justify-between'>
                                            <span className='text-gray-600'>
                                                Материал
                                            </span>
                                            <span className='font-medium'>
                                                кожа натуральная
                                            </span>
                                        </li>
                                        <li className='flex justify-between'>
                                            <span className='text-gray-600'>
                                                Бренд
                                            </span>
                                            <span className='font-medium'>
                                                {product.brand}
                                            </span>
                                        </li>
                                    </ul>
                                </div>
                                <div className='space-y-6'>
                                    <h2 className='text-xl font-bold'>
                                        Дополнительная информация
                                    </h2>
                                    <ul className='space-y-4'>
                                        <li className='flex justify-between'>
                                            <span className='text-gray-600'>
                                                Цвет
                                            </span>
                                            <span className='font-medium'>
                                                {product.color.value.join(', ')}
                                            </span>
                                        </li>
                                        <li className='flex justify-between'>
                                            <span className='text-gray-600'>
                                                Страна бренда
                                            </span>
                                            <span className='font-medium'>
                                                Россия
                                            </span>
                                        </li>
                                        <li className='flex justify-between'>
                                            <span className='text-gray-600'>
                                                Страна производства
                                            </span>
                                            <span className='font-medium'>
                                                РОССИЯ
                                            </span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case 'availability':
                const currentStores =
                    storeAvailabilityData.stores[
                        availabilitySelectedSize as keyof typeof storeAvailabilityData.stores
                    ] || [];

                return (
                    <div className='space-y-6 text-left'>
                        {/* Выбор размера для наличия */}
                        <div className='dimensions dimensions--type-1'>
                            <div className='dimensions__inner-wrapper'>
                                <div className='dimensions__nav nav-dimensions mb-6'>
                                    <span className='nav-dimensions__title font-medium mr-4'>
                                        Выберите размер:
                                    </span>
                                    <div className='nav-dimensions__list flex flex-wrap gap-2'>
                                        {storeAvailabilityData.sizes.map(
                                            (size) => (
                                                <div
                                                    key={size}
                                                    className={`nav-dimensions__item ${
                                                        availabilitySelectedSize ===
                                                        size
                                                            ? 'active'
                                                            : ''
                                                    } ${
                                                        !currentStores.length
                                                            ? 'disabled opacity-50'
                                                            : ''
                                                    }`}
                                                >
                                                    <button
                                                        className={`nav-dimensions__link px-4 py-2 border rounded-lg font-medium transition-colors ${
                                                            availabilitySelectedSize ===
                                                            size
                                                                ? 'bg-blue-500 text-white border-blue-500'
                                                                : 'bg-white text-gray-800 border-gray-300 hover:border-blue-500'
                                                        } ${!currentStores.length ? 'cursor-not-allowed' : ''}`}
                                                        onClick={() =>
                                                            currentStores.length &&
                                                            setAvailabilitySelectedSize(
                                                                size,
                                                            )
                                                        }
                                                        disabled={
                                                            !currentStores.length
                                                        }
                                                    >
                                                        <span>{size}</span>
                                                    </button>
                                                </div>
                                            ),
                                        )}
                                    </div>
                                </div>

                                <div className='dimensions__content content-dimensions'>
                                    <div className='content-dimensions__list'>
                                        <div className='content-dimensions__item active'>
                                            <div className='points'>
                                                <span className='points__title font-semibold text-lg block mb-4'>
                                                    Товар в наличии:
                                                </span>

                                                <ul className='points__list grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
                                                    {currentStores.map(
                                                        (store) => (
                                                            <li
                                                                key={store.id}
                                                                className='points__item'
                                                            >
                                                                <div className='points__link border border-gray-200 rounded-lg p-4 hover:border-blue-500 transition-colors cursor-pointer h-full'>
                                                                    <span className='points__description font-medium block mb-2'>
                                                                        {
                                                                            store.name
                                                                        }
                                                                    </span>
                                                                    <span className='points__phone text-sm text-gray-600 block mb-3'>
                                                                        тел.{' '}
                                                                        {
                                                                            store.phone
                                                                        }
                                                                    </span>

                                                                    {store.badges &&
                                                                        store
                                                                            .badges
                                                                            .length >
                                                                            0 && (
                                                                            <div className='points__wobbler mb-3'>
                                                                                {store.badges.map(
                                                                                    (
                                                                                        badge,
                                                                                        index,
                                                                                    ) => (
                                                                                        <span
                                                                                            key={
                                                                                                index
                                                                                            }
                                                                                            className={`points__badge px-2 py-1 text-xs rounded-full ${getBadgeClass(badge)}`}
                                                                                        >
                                                                                            {getBadgeText(
                                                                                                badge,
                                                                                            )}
                                                                                        </span>
                                                                                    ),
                                                                                )}
                                                                            </div>
                                                                        )}

                                                                    {store.metro &&
                                                                        store
                                                                            .metro
                                                                            .length >
                                                                            0 && (
                                                                            <div className='points__data data-points'>
                                                                                <ul className='data-points__list flex flex-wrap gap-1'>
                                                                                    {store.metro.map(
                                                                                        (
                                                                                            station,
                                                                                            index,
                                                                                        ) => (
                                                                                            <li
                                                                                                key={
                                                                                                    index
                                                                                                }
                                                                                                className={`data-points__item px-2 py-1 text-xs rounded ${getMetroColorClass(index)}`}
                                                                                            >
                                                                                                {
                                                                                                    station
                                                                                                }
                                                                                            </li>
                                                                                        ),
                                                                                    )}
                                                                                </ul>
                                                                            </div>
                                                                        )}
                                                                </div>
                                                            </li>
                                                        ),
                                                    )}

                                                    {/* Склад интернет-магазина */}
                                                    <li className='points__item'>
                                                        <div className='points__link points__link--type-1 border border-gray-200 rounded-lg p-4 bg-gray-50 h-full'>
                                                            <span className='points__description font-medium block mb-2'>
                                                                Склад
                                                                интернет-магазина
                                                            </span>
                                                            <span className='points__detail text-sm text-gray-600'>
                                                                Оформите заказ
                                                                на сайте и
                                                                получите товар с
                                                                доставкой или в
                                                                любом салоне.
                                                            </span>
                                                        </div>
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case 'delivery':
                return (
                    <div className='space-y-4 text-gray-600 text-left'>
                        <p>Доставка осуществляется во все города России.</p>
                        <p>
                            Вы можете выбрать доставку курьером, Почтой России
                            или получить в удобном вам пункте выдачи СДЭК.
                        </p>
                        <p>
                            Стоимость и примерные сроки доставки будут
                            рассчитаны во время оформления заказа.
                        </p>
                        <p>
                            Более подробную информацию можно узнать в разделе «
                            <a
                                href='/delivery/'
                                target='_blank'
                                className='text-blue-600 hover:underline'
                            >
                                Доставка
                            </a>
                            ».
                        </p>
                    </div>
                );

            case 'payment':
                return (
                    <div className='space-y-4 text-gray-600 text-left'>
                        <p>
                            Оплатить заказ вы можете любым из перечисленных
                            способов:
                        </p>
                        <ul className='list-disc list-inside space-y-2 ml-4'>
                            <li>
                                Банковской картой. Сразу после создания заказа
                                появится соответствующее окошко. Карта должна
                                быть доступна для совершения оплаты онлайн.
                            </li>
                            <li>
                                Банковским переводом по выставленному счету.
                            </li>
                            <li>
                                Наличными деньгами курьеру или в Салоне при
                                самовывозе заказа.
                            </li>
                        </ul>
                        <p>
                            Подробнее о способах оплаты Вы можете узнать в
                            разделе «
                            <a
                                href='/payment/'
                                target='_blank'
                                className='text-blue-600 hover:underline'
                            >
                                Оплата
                            </a>
                            ».
                        </p>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className='container mx-auto px-4 py-8'>
            <Breadcrumbs items={breadcrumbItems} />

            <div className='max-w-7xl mx-auto'>
                <div className='grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12'>
                    {/* Левая колонка - галерея изображений */}
                    <div>
                        <div className='flex flex-col lg:flex-row gap-4'>
                            {/* Миниатюры слева */}
                            <div className='order-2 lg:order-1'>
                                <div className='flex lg:flex-col gap-2 overflow-x-auto lg:overflow-x-visible max-w-full lg:max-w-[90px]'>
                                    {productGalleryImages.map(
                                        (image, index) => (
                                            <ThumbnailCard
                                                key={index}
                                                image={image}
                                                alt={`${product.alt} ${index + 1}`}
                                                isActive={mainImage === image}
                                                onClick={() =>
                                                    setMainImage(image)
                                                }
                                            />
                                        ),
                                    )}
                                </div>
                            </div>

                            {/* Основное изображение справа */}
                            <div className='order-1 lg:order-2 flex-1'>
                                <div className='relative'>
                                    {/* Бейджи */}
                                    {activeBadges.length > 0 && (
                                        <div className='absolute top-3 left-3 z-10'>
                                            <div className='flex flex-col gap-1'>
                                                {activeBadges.map(
                                                    (badge, index) => (
                                                        <div
                                                            key={index}
                                                            className='bg-red-500 text-white px-2 py-1 rounded text-xs font-bold'
                                                        >
                                                            {badge}
                                                        </div>
                                                    ),
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Кнопка избранного */}
                                    <div className='absolute top-3 right-3 z-10'>
                                        <button
                                            type='button'
                                            className={`p-2 rounded-full ${
                                                isInWishlist
                                                    ? 'bg-red-500 text-white'
                                                    : 'bg-white text-gray-600 border border-gray-300'
                                            }`}
                                            onClick={handleToggleWishlist}
                                            title={
                                                isInWishlist
                                                    ? 'Удалить товар из избранного'
                                                    : 'Добавить товар в избранное'
                                            }
                                        >
                                            ❤
                                        </button>
                                    </div>

                                    {/* Основное изображение */}
                                    <img
                                        src={`${domain}${mainImage}`}
                                        alt={product.alt}
                                        className='w-full h-auto rounded-lg shadow-lg'
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Правая колонка - информация о товаре */}
                    <div>
                        {/* Заголовок и код товара */}
                        <div className='mb-6 text-left'>
                            <h1 className='text-2xl lg:text-3xl font-bold text-gray-900 mb-2'>
                                {product.title}
                            </h1>
                            <div className='flex items-center gap-4'>
                                <span className='text-sm text-gray-500'>
                                    Код товара:{' '}
                                    {product.id.replace('prod', 'ЦУ-')}
                                </span>
                                <span className='text-sm text-gray-500'>
                                    Бренд: {product.brand}
                                </span>
                            </div>
                        </div>

                        {/* Блок с акцией */}
                        <div className='bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 text-left'>
                            <div className='font-bold text-yellow-800 mb-1'>
                                КИБЕРДНИ! С 5 по 7 ноября
                            </div>
                            <div className='text-yellow-700'>
                                <p>СКИДКИ на всю обувь и сумки до -40%!</p>
                            </div>
                        </div>

                        {/* Выбор размера */}
                        <div className='mb-6 text-left'>
                            <div className='flex justify-between items-center mb-4'>
                                <span className='font-semibold'>
                                    Выберите размер:
                                </span>
                                <a
                                    href='#'
                                    className='text-blue-600 text-sm hover:underline'
                                >
                                    как{' '}
                                    <span className='font-semibold'>
                                        правильно
                                    </span>{' '}
                                    подобрать размер
                                </a>
                            </div>

                            {/* Список размеров */}
                            <div className='flex flex-wrap gap-2 mb-4'>
                                {product.sizes.map((size) => (
                                    <button
                                        key={size}
                                        className={`px-4 py-2 border rounded-lg font-semibold transition-colors ${
                                            selectedSize === size
                                                ? 'bg-blue-500 text-white border-blue-500'
                                                : 'bg-white text-gray-800 border-gray-300 hover:border-blue-500'
                                        }`}
                                        onClick={() => setSelectedSize(size)}
                                    >
                                        {size}
                                    </button>
                                ))}
                            </div>

                            {/* Цена и кнопки */}
                            <div className='mb-4'>
                                {product.price.old && (
                                    <span className='text-lg text-gray-500 line-through mr-2'>
                                        {product.price.old}
                                    </span>
                                )}
                                <span className='text-3xl font-bold text-gray-900'>
                                    {product.price.current}
                                </span>
                            </div>

                            {/* Кнопки действий */}
                            <div className='grid grid-cols-1 lg:grid-cols-2 gap-3 mb-6'>
                                <div>
                                    {!isInCart ? (
                                        <button
                                            className='w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors'
                                            onClick={handleAddToCart}
                                        >
                                            Добавить в корзину
                                        </button>
                                    ) : (
                                        <a
                                            href='/cart/'
                                            className='w-full bg-green-600 text-white py-3 px-6 rounded-lg font-medium text-center block hover:bg-green-700 transition-colors'
                                        >
                                            В корзине
                                        </a>
                                    )}
                                </div>
                                <div>
                                    <button
                                        className='w-full bg-white text-blue-600 border border-blue-600 py-3 px-6 rounded-lg font-medium hover:bg-blue-50 transition-colors'
                                        onClick={handleOneClickBuy}
                                    >
                                        Купить в 1 клик
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Информация о кредите */}
                        <div className='bg-gray-50 rounded-lg p-4 mb-6 text-left'>
                            <div className='flex justify-between items-center mb-3'>
                                <span className='text-xl font-bold'>
                                    10 194 ₽
                                </span>
                                <img
                                    src='https://cdn.podeli.ru/common-img/logo-left-text.svg'
                                    alt='Логотип'
                                    className='h-6'
                                />
                            </div>
                            <div className='text-sm text-gray-600'>
                                Без комиссий и переплат
                            </div>
                        </div>

                        {/* Бейджи доверия */}
                        <div className='mb-6 text-left'>
                            <div className='flex gap-4'>
                                <img
                                    src={`${domain}/upload/images/badges/eac.svg`}
                                    alt='EAC'
                                    className='h-8'
                                    title='Только оригинальные товары с декларациями соответствия'
                                />
                                <img
                                    src={`${domain}/upload/images/badges/honest-sign.svg`}
                                    alt='Честный знак'
                                    className='h-8'
                                    title='Вся обувь с маркировкой «Честный знак»'
                                />
                                <img
                                    src={`${domain}/upload/images/badges/alfabank.svg`}
                                    alt='Альфа-Банк'
                                    className='h-8'
                                    title='Безопасная оплата без комиссии'
                                />
                            </div>
                        </div>
                    </div>
                    {/* Табы с описанием товара */}
                    <div className='pt-6 border-t border-gray-200 text-left'>
                        {/* Навигация табов */}
                        <div className='border-b border-gray-200 mb-6'>
                            <div className='flex flex-wrap gap-4'>
                                {[
                                    {
                                        id: 'characteristics',
                                        label: 'Характеристики',
                                    },
                                    {
                                        id: 'availability',
                                        label: 'Наличие в магазинах',
                                    },
                                    { id: 'delivery', label: 'Доставка' },
                                    { id: 'payment', label: 'Оплата' },
                                ].map((tab) => (
                                    <button
                                        key={tab.id}
                                        className={`pb-3 px-1 font-medium transition-colors border-b-2 ${
                                            activeTab === tab.id
                                                ? 'border-blue-500 text-blue-600'
                                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                        }`}
                                        onClick={() => setActiveTab(tab.id)}
                                    >
                                        {tab.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Контент табов */}
                        <div className='min-h-[200px]'>
                            {renderTabContent()}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
