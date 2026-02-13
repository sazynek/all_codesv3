import { createFileRoute } from '@tanstack/react-router';
import { Breadcrumbs } from '../../components/ui/Breadcrumbs';

export const Route = createFileRoute('/promos/')({
    component: PromosPage,
});

// Тип для акции
interface PromoItem {
    id: string;
    title: string;
    url: string;
    image: string;
    alt: string;
}

// Моковые данные для акций (можно заменить на реальные из API)
const promosData: PromoItem[] = [
    {
        id: '1',
        title: 'Дни шопинга в сети салонов',
        url: '/promos/dni-shopinga-v-seti-salonov2/',
        image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/a23/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/mgva96oo9c3pj5keektnmayum014ar5w.jpg',
        alt: 'Дни шопинга в сети салонов',
    },
    {
        id: '2',
        title: '2=10%; 3=20% на НОВИНКИ',
        url: '/promos/2-10-3-20-na-novinki/',
        image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/204/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/pgolq3l49ymo6xmuz4bsf6iz2qhr0z09.jpg',
        alt: '2=10%; 3=20% на НОВИНКИ',
    },
    {
        id: '3',
        title: 'Лучшая цена!',
        url: '/promos/luchshaya-tsena-na-izbrannye-modeli24/',
        image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/647/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/ys18ff1tme5wjiz1zrlxebe4ux0aa4tj.jpg',
        alt: 'Лучшая цена!',
    },
    {
        id: '4',
        title: 'Поделите покупку на 4 платежа!',
        url: '/promos/podelite-pokupku-na-4-platezha/',
        image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/2a9/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/k2nbzhdg2irgxbn5398u2gdsd14r8a3h.jpg',
        alt: 'Поделите покупку на 4 платежа!',
    },
    {
        id: '5',
        title: '300 рублей на первую покупку',
        url: '/promos/300-rubley-na-pervuyu-pokupku/',
        image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/468/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/z6kqeku9fhp830fj2fi5qqawbmgwdnu2.jpg',
        alt: '300 рублей на первую покупку',
    },
    {
        id: '6',
        title: 'Подарочные карты',
        url: '/promos/podarochnye-karty/',
        image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/c0a/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/1cy9h9tw1zeb0v8z3oh2p4lxxuvdrhhv.jpg',
        alt: 'Подарочные карты',
    },
];

export function PromosPage() {
    const breadcrumbItems = [
        { label: 'Главная', href: '/' },
        { label: 'Акции', href: '/promos/' },
    ];

    return (
        <div className='w-full py-8'>
            {/* Контейнер с фиксированной шириной как на оригинальном сайте */}
            <div className='w-[1410px] mx-auto px-4'>
                {/* Хлебные крошки */}
                <Breadcrumbs items={breadcrumbItems} />

                {/* Сетка акций - 2 колонки с точными размерами */}
                <main className='main'>
                    <div className='stock'>
                        <ul className='grid grid-cols-2 gap-8'>
                            {promosData.map((promo) => (
                                <li key={promo.id} className='stock__item'>
                                    <a
                                        href={promo.url}
                                        className='stock__link block group'
                                    >
                                        {/* Контейнер изображения с точными размерами */}
                                        <div className='w-[689px] h-[339px] overflow-hidden rounded-lg shadow-md transition-all duration-300 group-hover:shadow-xl group-hover:scale-[1.01]'>
                                            <img
                                                src={promo.image}
                                                alt={promo.alt}
                                                className='w-full h-full object-cover'
                                                width={689}
                                                height={339}
                                                loading='lazy'
                                            />
                                        </div>
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                </main>
            </div>

            {/* Schema.org разметка */}
            <script
                type='application/ld+json'
                dangerouslySetInnerHTML={{
                    __html: JSON.stringify({
                        '@context': 'http://schema.org',
                        '@type': 'BreadcrumbList',
                        itemListElement: [
                            {
                                '@type': 'ListItem',
                                position: 1,
                                item: {
                                    '@id': 'https://www.немецкаяобувь.com/',
                                    name: 'Главная',
                                },
                            },
                            {
                                '@type': 'ListItem',
                                position: 2,
                                item: {
                                    '@id': 'https://www.немецкаяобувь.com/promos/',
                                    name: 'Акции',
                                },
                            },
                        ],
                    }),
                }}
            />
        </div>
    );
}
