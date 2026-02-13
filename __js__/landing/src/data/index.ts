import type {
    BreadcrumbItem,
    Category,
    CategoryDataResult,
    FilterAttributes,
    FilterBrand,
    FilterColor,
    FilterParams,
    FilterSection,
    FilterSpecial,
    Product,
    ProductCategory,
    ProductDataResult,
    BrandDataResult,
    BrandItem,
    BrandsDataResult,
} from '../types';

// database.ts
export const database = {
    categories: [
        // ==================== КОРНЕВЫЕ КАТЕГОРИИ ====================
        {
            id: 'cat1',
            name: 'Женская обувь',
            slug: 'zhenskaya-obuv',
            parent_id: null,
            path: 'zhenskaya-obuv',
            level: 0,
            sort_order: 1,
        },
        {
            id: 'cat2',
            name: 'Мужская обувь',
            slug: 'muzhskaya-obuv',
            parent_id: null,
            path: 'muzhskaya-obuv',
            level: 0,
            sort_order: 2,
        },
        {
            id: 'cat3',
            name: 'Сумки',
            slug: 'sumki',
            parent_id: null,
            path: 'sumki',
            level: 0,
            sort_order: 3,
        },
        {
            id: 'cat4',
            name: 'Аксессуары',
            slug: 'aksessuary',
            parent_id: null,
            path: 'aksessuary',
            level: 0,
            sort_order: 4,
        },

        // ==================== ЖЕНСКАЯ ОБУВЬ - Уровень 1 ====================
        {
            id: 'cat101',
            name: '⚡ ЛУЧШАЯ ЦЕНА',
            slug: '-128293-spetsialnaya-tsena',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/-128293-spetsialnaya-tsena',
            level: 1,
            sort_order: 1,
            is_special: true,
        },
        {
            id: 'cat102',
            name: 'НОВИНКИ',
            slug: 'novinki',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/novinki',
            level: 1,
            sort_order: 2,
            is_special: true,
        },
        {
            id: 'cat103',
            name: 'Балетки',
            slug: 'baletki',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/baletki',
            level: 1,
            sort_order: 3,
        },
        {
            id: 'cat104',
            name: 'Босоножки',
            slug: 'bosonozhki',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/bosonozhki',
            level: 1,
            sort_order: 4,
        },
        {
            id: 'cat105',
            name: 'Ботильоны',
            slug: 'botilony',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/botilony',
            level: 1,
            sort_order: 5,
        },
        {
            id: 'cat106',
            name: 'Ботинки',
            slug: 'botinki',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/botinki',
            level: 1,
            sort_order: 6,
        },
        {
            id: 'cat107',
            name: 'Ботфорты',
            slug: 'botforty',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/botforty',
            level: 1,
            sort_order: 7,
        },
        {
            id: 'cat108',
            name: 'Домашняя обувь',
            slug: 'tapochki',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/tapochki',
            level: 1,
            sort_order: 8,
        },
        {
            id: 'cat109',
            name: 'Кроссовки',
            slug: 'krossovki',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/krossovki',
            level: 1,
            sort_order: 9,
        },
        {
            id: 'cat110',
            name: 'Лоферы',
            slug: 'lofery',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/lofery',
            level: 1,
            sort_order: 10,
        },
        {
            id: 'cat111',
            name: 'Мокасины',
            slug: 'mokasiny',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/mokasiny',
            level: 1,
            sort_order: 11,
        },
        {
            id: 'cat112',
            name: 'Полуботинки',
            slug: 'polubotinki',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/polubotinki',
            level: 1,
            sort_order: 12,
        },
        {
            id: 'cat113',
            name: 'Полусапоги',
            slug: 'polusapogi',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/polusapogi',
            level: 1,
            sort_order: 13,
        },
        {
            id: 'cat114',
            name: 'Сабо',
            slug: 'sabo',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/sabo',
            level: 1,
            sort_order: 14,
        },
        {
            id: 'cat115',
            name: 'Сандалии',
            slug: 'sandalii',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/sandalii',
            level: 1,
            sort_order: 15,
        },
        {
            id: 'cat116',
            name: 'Сапоги',
            slug: 'sapogi',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/sapogi',
            level: 1,
            sort_order: 16,
        },
        {
            id: 'cat117',
            name: 'Туфли',
            slug: 'tufli',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/tufli',
            level: 1,
            sort_order: 17,
        },
        {
            id: 'cat118',
            name: 'SALE',
            slug: '-128293-spetsialnoe-predlozhenie',
            parent_id: 'cat1',
            path: 'zhenskaya-obuv/-128293-spetsialnoe-predlozhenie',
            level: 1,
            sort_order: 18,
            is_special: true,
        },

        // Подкатегории туфель (Уровень 2)
        {
            id: 'cat119',
            name: 'Туфли закрытые',
            slug: 'zakrytye',
            parent_id: 'cat117',
            path: 'zhenskaya-obuv/tufli/zakrytye',
            level: 2,
            sort_order: 1,
        },

        // ==================== МУЖСКАЯ ОБУВЬ - Уровень 1 ====================
        {
            id: 'cat201',
            name: '⚡ ЛУЧШАЯ ЦЕНА',
            slug: '-128293-spetsialnaya-tsena',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/-128293-spetsialnaya-tsena',
            level: 1,
            sort_order: 1,
            is_special: true,
        },
        {
            id: 'cat202',
            name: 'НОВИНКИ',
            slug: 'novinki',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/novinki',
            level: 1,
            sort_order: 2,
            is_special: true,
        },
        {
            id: 'cat203',
            name: 'Ботинки',
            slug: 'botinki',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/botinki',
            level: 1,
            sort_order: 3,
        },
        {
            id: 'cat204',
            name: 'Кроссовки',
            slug: 'krossovki',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/krossovki',
            level: 1,
            sort_order: 4,
        },
        {
            id: 'cat205',
            name: 'Лоферы',
            slug: 'lofery',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/lofery',
            level: 1,
            sort_order: 5,
        },
        {
            id: 'cat206',
            name: 'Мокасины',
            slug: 'mokasiny',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/mokasiny',
            level: 1,
            sort_order: 6,
        },
        {
            id: 'cat207',
            name: 'Полуботинки',
            slug: 'polubotinki',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/polubotinki',
            level: 1,
            sort_order: 7,
        },
        {
            id: 'cat208',
            name: 'Туфли',
            slug: 'tufli',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/tufli',
            level: 1,
            sort_order: 8,
        },
        {
            id: 'cat209',
            name: 'Сланцы',
            slug: 'slantsy',
            parent_id: 'cat2',
            path: 'muzhskaya-obuv/slantsy',
            level: 1,
            sort_order: 9,
        },

        // ==================== СУМКИ - Уровень 1 ====================
        {
            id: 'cat301',
            name: '⚡ ЛУЧШАЯ ЦЕНА',
            slug: '-128293-spetsialnaya-tsena',
            parent_id: 'cat3',
            path: 'sumki/-128293-spetsialnaya-tsena',
            level: 1,
            sort_order: 1,
            is_special: true,
        },
        {
            id: 'cat302',
            name: 'НОВИНКИ',
            slug: 'novinki',
            parent_id: 'cat3',
            path: 'sumki/novinki',
            level: 1,
            sort_order: 2,
            is_special: true,
        },
        {
            id: 'cat303',
            name: 'Женские сумки',
            slug: 'sumki-zhenskie',
            parent_id: 'cat3',
            path: 'sumki/sumki-zhenskie',
            level: 1,
            sort_order: 3,
        },
        {
            id: 'cat304',
            name: 'Мужские сумки',
            slug: 'sumki-muzhskie',
            parent_id: 'cat3',
            path: 'sumki/sumki-muzhskie',
            level: 1,
            sort_order: 4,
        },
        {
            id: 'cat305',
            name: 'Рюкзаки',
            slug: 'ryukzaki',
            parent_id: 'cat3',
            path: 'sumki/ryukzaki',
            level: 1,
            sort_order: 5,
        },
        {
            id: 'cat306',
            name: 'Клатчи',
            slug: 'klatchi',
            parent_id: 'cat3',
            path: 'sumki/klatchi',
            level: 1,
            sort_order: 6,
        },

        // Подкатегории сумок (Уровень 2)
        {
            id: 'cat307',
            name: 'Маленькие сумки',
            slug: 'malenkie',
            parent_id: 'cat303',
            path: 'sumki/sumki-zhenskie/malenkie',
            level: 2,
            sort_order: 1,
        },
        {
            id: 'cat308',
            name: 'Средние сумки',
            slug: 'srednie',
            parent_id: 'cat303',
            path: 'sumki/sumki-zhenskie/srednie',
            level: 2,
            sort_order: 2,
        },
        {
            id: 'cat309',
            name: 'Большие сумки',
            slug: 'bolshie',
            parent_id: 'cat303',
            path: 'sumki/sumki-zhenskie/bolshie',
            level: 2,
            sort_order: 3,
        },
        {
            id: 'cat310',
            name: 'Кожаные сумки',
            slug: 'kozhanye',
            parent_id: 'cat304',
            path: 'sumki/sumki-muzhskie/kozhanye',
            level: 2,
            sort_order: 1,
        },
        {
            id: 'cat311',
            name: 'Спортивные сумки',
            slug: 'sportivnye',
            parent_id: 'cat304',
            path: 'sumki/sumki-muzhskie/sportivnye',
            level: 2,
            sort_order: 2,
        },
        {
            id: 'cat312',
            name: 'Городские рюкзаки',
            slug: 'gorodskie',
            parent_id: 'cat305',
            path: 'sumki/ryukzaki/gorodskie',
            level: 2,
            sort_order: 1,
        },
        {
            id: 'cat313',
            name: 'Туристические рюкзаки',
            slug: 'turisticheskie',
            parent_id: 'cat305',
            path: 'sumki/ryukzaki/turisticheskie',
            level: 2,
            sort_order: 2,
        },

        // ==================== АКСЕССУАРЫ - Уровень 1 ====================
        {
            id: 'cat401',
            name: '⚡ ЛУЧШАЯ ЦЕНА',
            slug: '-128293-spetsialnaya-tsena',
            parent_id: 'cat4',
            path: 'aksessuary/-128293-spetsialnaya-tsena',
            level: 1,
            sort_order: 1,
            is_special: true,
        },
        {
            id: 'cat402',
            name: 'НОВИНКИ',
            slug: 'novinki',
            parent_id: 'cat4',
            path: 'aksessuary/novinki',
            level: 1,
            sort_order: 2,
            is_special: true,
        },
        {
            id: 'cat403',
            name: 'Ремни',
            slug: 'remni',
            parent_id: 'cat4',
            path: 'aksessuary/remni',
            level: 1,
            sort_order: 3,
        },
        {
            id: 'cat404',
            name: 'Кошельки',
            slug: 'koshelki',
            parent_id: 'cat4',
            path: 'aksessuary/koshelki',
            level: 1,
            sort_order: 4,
        },
        {
            id: 'cat405',
            name: 'Перчатки',
            slug: 'perchatki',
            parent_id: 'cat4',
            path: 'aksessuary/perchatki',
            level: 1,
            sort_order: 5,
        },
        {
            id: 'cat406',
            name: 'Зонты',
            slug: 'zonty',
            parent_id: 'cat4',
            path: 'aksessuary/zonty',
            level: 1,
            sort_order: 6,
        },

        // Подкатегории аксессуаров (Уровень 2)
        {
            id: 'cat407',
            name: 'Кожаные ремни',
            slug: 'kozhanye',
            parent_id: 'cat403',
            path: 'aksessuary/remni/kozhanye',
            level: 2,
            sort_order: 1,
        },
        {
            id: 'cat408',
            name: 'Тканые ремни',
            slug: 'tkanye',
            parent_id: 'cat403',
            path: 'aksessuary/remni/tkanye',
            level: 2,
            sort_order: 2,
        },
        {
            id: 'cat409',
            name: 'Мужские кошельки',
            slug: 'muzhskie',
            parent_id: 'cat404',
            path: 'aksessuary/koshelki/muzhskie',
            level: 2,
            sort_order: 1,
        },
        {
            id: 'cat410',
            name: 'Женские кошельки',
            slug: 'zhenskie',
            parent_id: 'cat404',
            path: 'aksessuary/koshelki/zhenskie',
            level: 2,
            sort_order: 2,
        },
        {
            id: 'cat411',
            name: 'Кожаные перчатки',
            slug: 'kozhanye',
            parent_id: 'cat405',
            path: 'aksessuary/perchatki/kozhanye',
            level: 2,
            sort_order: 1,
        },
        {
            id: 'cat412',
            name: 'Трикотажные перчатки',
            slug: 'triko',
            parent_id: 'cat405',
            path: 'aksessuary/perchatki/triko',
            level: 2,
            sort_order: 2,
        },
        {
            id: 'cat413',
            name: 'Автоматические зонты',
            slug: 'avtomaticheskie',
            parent_id: 'cat406',
            path: 'aksessuary/zonty/avtomaticheskie',
            level: 2,
            sort_order: 1,
        },
        {
            id: 'cat414',
            name: 'Складные зонты',
            slug: 'skladnye',
            parent_id: 'cat406',
            path: 'aksessuary/zonty/skladnye',
            level: 2,
            sort_order: 2,
        },
    ] as Category[],

    products: [
        // Женская обувь - 15 товаров
        {
            id: 'prod101',
            title: 'Ботинки женские кожаные ARA',
            url: '/category/zhenskaya-obuv/botinki_zhenskie_prod101/',
            image: '/upload/resize_cache/iblock/7f1/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/norbrbwd7ba7mnk1ybjvbfmhpj63qvbj.jpg',
            alt: 'Ботинки женские ARA',
            price: { old: '17 990 руб.', current: '14 392 руб.' },
            brand: 'ARA',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [36, 37, 38, 39, 40],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod102',
            title: 'Кроссовки женские спортивные',
            url: '/category/zhenskaya-obuv/krossovki_zhenskie_prod102/',
            image: '/upload/resize_cache/iblock/9f0/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/vkte625en5taefng64sl1dr84wuttoe0.jpg',
            alt: 'Кроссовки женские',
            price: { old: '12 990 руб.', current: '9 990 руб.' },
            brand: 'CAPRICE',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: true, value: 'HIT' },
            },
            color: { is_one: true, value: ['white'] },
            sizes: [35, 36, 37, 38, 39],
            is_discount: { active: true, value: 23 },
        },
        {
            id: 'prod103',
            title: 'Туфли женские закрытые',
            url: '/category/zhenskaya-obuv/tufli/zakrytye/tufli_prod103/',
            image: '/upload/resize_cache/iblock/2bf/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/uclcczgr39us37wsjn6uyq9nhqazk81i.jpg',
            alt: 'Туфли женские закрытые',
            price: { current: '8 490 руб.' },
            brand: 'RIEKER',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['beige'] },
            sizes: [36, 37, 38, 39],
            is_discount: { active: false, value: 0 },
        },
        {
            id: 'prod104',
            title: 'Сапоги женские зимние',
            url: '/category/zhenskaya-obuv/sapogi_zhenskie_prod104/',
            image: '/upload/resize_cache/iblock/2e9/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/ruwe2tw8wp19rm4fkk5198xuctyfy7ex.jpg',
            alt: 'Сапоги женские',
            price: { old: '15 990 руб.', current: '12 792 руб.' },
            brand: 'SUAVE',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [36, 37, 38, 39, 40],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod105',
            title: 'Босоножки женские летние',
            url: '/category/zhenskaya-obuv/bosonozhki_zhenskie_prod105/',
            image: '/upload/resize_cache/iblock/b8a/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/51qpoyy0lb32h8cbmfu3g1rvy4msppy1.jpg',
            alt: 'Босоножки женские',
            price: { current: '6 990 руб.' },
            brand: 'KELTON',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: true, value: 'HIT' },
            },
            color: { is_one: true, value: ['gold'] },
            sizes: [35, 36, 37, 38],
            is_discount: { active: false, value: 0 },
        },
        {
            id: 'prod106',
            title: 'Балетки женские классические',
            url: '/category/zhenskaya-obuv/baletki_zhenskie_prod106/',
            image: '/upload/resize_cache/iblock/67a/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/a08roepdk06ekxky72yg2s27rzbs47qz.jpg',
            alt: 'Балетки женские',
            price: { old: '5 990 руб.', current: '4 492 руб.' },
            brand: 'ARA',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [36, 37, 38, 39],
            is_discount: { active: true, value: 25 },
        },
        {
            id: 'prod107',
            title: 'Лоферы женские кожаные',
            url: '/category/zhenskaya-obuv/lofery_zhenskie_prod107/',
            image: '/upload/resize_cache/iblock/b4e/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/jho6rqois4fdzmj0hmjglfb5rwue9h7t.jpg',
            alt: 'Лоферы женские',
            price: { current: '11 990 руб.' },
            brand: 'CAPRICE',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [36, 37, 38, 39, 40],
            is_discount: { active: false, value: 0 },
        },
        {
            id: 'prod108',
            title: 'Мокасины женские удобные',
            url: '/category/zhenskaya-obuv/mokasiny_zhenskie_prod108/',
            image: '/upload/resize_cache/iblock/7e1/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/afsalg4aj2mk6m6np3p0lhqu4ncxrq0e.jpg',
            alt: 'Мокасины женские',
            price: { old: '8 990 руб.', current: '6 742 руб.' },
            brand: 'RIEKER',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['blue'] },
            sizes: [36, 37, 38, 39],
            is_discount: { active: true, value: 25 },
        },
        {
            id: 'prod109',
            title: 'Полуботинки женские осенние',
            url: '/category/zhenskaya-obuv/polubotinki_zhenskie_prod109/',
            image: '/upload/resize_cache/iblock/7fc/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/rdhw2ngr3511vdo3rw8mlv3iacgn539v.jpg',
            alt: 'Полуботинки женские',
            price: { current: '9 490 руб.' },
            brand: 'SUAVE',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['gray'] },
            sizes: [36, 37, 38, 39, 40],
            is_discount: { active: false, value: 0 },
        },
        {
            id: 'prod110',
            title: 'Сандалии женские пляжные',
            url: '/category/zhenskaya-obuv/sandalii_zhenskie_prod110/',
            image: '/upload/resize_cache/iblock/9ed/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/z9uk0dk2hip0cyjc4ops87ee6l6izq46.jpg',
            alt: 'Сандалии женские',
            price: { old: '4 990 руб.', current: '3 492 руб.' },
            brand: 'KELTON',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['pink'] },
            sizes: [35, 36, 37, 38],
            is_discount: { active: true, value: 30 },
        },
        {
            id: 'prod111',
            title: 'Ботильоны женские замшевые',
            url: '/category/zhenskaya-obuv/botilony_zhenskie_prod111/',
            image: '/upload/resize_cache/iblock/116/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/qh9k7nf2irdbi5eh3aym27vvgxykmclj.jpg',
            alt: 'Ботильоны женские',
            price: { current: '12 990 руб.' },
            brand: 'ARA',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['burgundy'] },
            sizes: [36, 37, 38, 39],
            is_discount: { active: false, value: 0 },
        },
        {
            id: 'prod112',
            title: 'Ботфорты женские высокие',
            url: '/category/zhenskaya-obuv/botforty_zhenskie_prod112/',
            image: '/upload/resize_cache/iblock/f6c/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/8fhylw8zp2apit71ssmb3cyoiotdnaa3.jpg',
            alt: 'Ботфорты женские',
            price: { old: '18 990 руб.', current: '15 192 руб.' },
            brand: 'CAPRICE',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [36, 37, 38, 39, 40],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod113',
            title: 'Домашняя обувь тапочки',
            url: '/category/zhenskaya-obuv/tapochki_zhenskie_prod113/',
            image: '/upload/resize_cache/iblock/f47/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/q5njpdyz6z3gfoxblm3feavs4i41ly7n.jpg',
            alt: 'Домашняя обувь',
            price: { current: '2 990 руб.' },
            brand: 'RIEKER',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: true, value: 'HIT' },
            },
            color: { is_one: false, value: ['red', 'blue', 'green'] },
            sizes: [36, 37, 38, 39, 40],
            is_discount: { active: false, value: 0 },
        },
        {
            id: 'prod114',
            title: 'Сабо женские летние',
            url: '/category/zhenskaya-obuv/sabo_zhenskie_prod114/',
            image: '/upload/resize_cache/iblock/506/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/f3c8r8n4hxqoc9vyr70tdm9isasvhdmh.jpg',
            alt: 'Сабо женские',
            price: { old: '6 490 руб.', current: '5 192 руб.' },
            brand: 'SUAVE',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['white'] },
            sizes: [36, 37, 38, 39],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod115',
            title: 'Полусапоги женские демисезонные',
            url: '/category/zhenskaya-obuv/polusapogi_zhenskie_prod115/',
            image: '/upload/resize_cache/iblock/439/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/bvcnf9wmdb1r78nq4vtvast27o62g9b1.jpg',
            alt: 'Полусапоги женские',
            price: { current: '10 990 руб.' },
            brand: 'KELTON',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['beige'] },
            sizes: [36, 37, 38, 39, 40],
            is_discount: { active: false, value: 0 },
        },

        // Мужская обувь - 15 товаров
        {
            id: 'prod201',
            title: 'Кроссовки мужские ARA',
            url: '/category/muzhskaya-obuv/krossovki_muzhskie_prod201/',
            image: '/upload/resize_cache/iblock/78f/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/p0r4ws31ducied99dgm0ja8eoa53cbfq.jpg',
            alt: 'Кроссовки мужские ARA',
            price: { old: '15 590 руб.', current: '12 472 руб.' },
            brand: 'ARA',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [40, 41, 42, 43, 44],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod202',
            title: 'Кроссовки мужские CAPRICE',
            url: '/category/muzhskaya-obuv/krossovki_muzhskie_prod202/',
            image: '/upload/resize_cache/iblock/649/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/hktrx1ag4ldmxx8pufm5i2997wcsbell.jpg',
            alt: 'Кроссовки мужские CAPRICE',
            price: { old: '15 590 руб.', current: '12 472 руб.' },
            brand: 'CAPRICE',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['gray'] },
            sizes: [41, 42, 43, 44, 45],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod203',
            title: 'Полуботинки мужские RIEKER',
            url: '/category/muzhskaya-obuv/polubotinki_muzhskie_prod203/',
            image: '/upload/resize_cache/iblock/737/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/nr8qrito4zl43e00l59occwvssgdt9ca.jpg',
            alt: 'Полуботинки мужские RIEKER',
            price: { old: '5 990 руб.', current: '3 594 руб.' },
            brand: 'RIEKER',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [40, 41, 42, 43],
            is_discount: { active: true, value: 40 },
        },
        {
            id: 'prod204',
            title: 'Ботинки мужские SUAVE',
            url: '/category/muzhskaya-obuv/botinki_muzhskie_prod204/',
            image: '/upload/resize_cache/iblock/7d8/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/1jphbaxt609rdq375q53zy2ugj4e2ro4.jpg',
            alt: 'Ботинки мужские SUAVE',
            price: { old: '19 990 руб.', current: '11 994 руб.' },
            brand: 'SUAVE',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [41, 42, 43, 44, 45],
            is_discount: { active: true, value: 40 },
        },
        {
            id: 'prod205',
            title: 'Ботинки мужские KELTON',
            url: '/category/muzhskaya-obuv/botinki_muzhskie_prod205/',
            image: '/upload/resize_cache/iblock/a7f/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/lc0puw6zc3kd8or21nequz1z83cjhcn0.jpg',
            alt: 'Ботинки мужские KELTON',
            price: { old: '20 990 руб.', current: '12 594 руб.' },
            brand: 'KELTON',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [40, 41, 42, 43, 44],
            is_discount: { active: true, value: 40 },
        },
        {
            id: 'prod206',
            title: 'Ботинки мужские ARA',
            url: '/category/muzhskaya-obuv/botinki_muzhskie_prod206/',
            image: '/upload/resize_cache/iblock/89f/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/qfoqal188bg3km4a8etu6uk7qr75m5oe.jpg',
            alt: 'Ботинки мужские ARA',
            price: { old: '19 990 руб.', current: '17 991 руб.' },
            brand: 'ARA',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['dark-brown'] },
            sizes: [42, 43, 44, 45],
            is_discount: { active: true, value: 10 },
        },
        {
            id: 'prod207',
            title: 'Ботинки мужские CAPRICE',
            url: '/category/muzhskaya-obuv/botinki_muzhskie_prod207/',
            image: '/upload/resize_cache/iblock/fe0/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/zdnmxmo3kwnzvja1t4mmj6zj5ppnw344.jpg',
            alt: 'Ботинки мужские CAPRICE',
            price: { old: '16 990 руб.', current: '13 592 руб.' },
            brand: 'CAPRICE',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [41, 42, 43, 44],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod208',
            title: 'Ботинки мужские RIEKER',
            url: '/category/muzhskaya-obuv/novinki/botinki_muzhskie_prod208/',
            image: '/upload/resize_cache/iblock/bf5/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/ok00mgebdczhcz7vtgt9brsw99x1qrli.jpg',
            alt: 'Ботинки мужские RIEKER',
            price: { old: '22 990 руб.', current: '18 392 руб.' },
            brand: 'RIEKER',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [40, 41, 42, 43, 44, 45],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod209',
            title: 'Ботинки мужские SUAVE',
            url: '/category/muzhskaya-obuv/botinki_muzhskie_prod209/',
            image: '/upload/resize_cache/iblock/6b1/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/ctmlhzjdrjwievhxueivczzfl3ss3wl5.jpg',
            alt: 'Ботинки мужские SUAVE',
            price: { old: '22 990 руб.', current: '18 392 руб.' },
            brand: 'SUAVE',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [41, 42, 43, 44],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod210',
            title: 'Ботинки мужские KELTON',
            url: '/category/muzhskaya-obuv/botinki_muzhskie_prod210/',
            image: '/upload/resize_cache/iblock/78f/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/p0r4ws31ducied99dgm0ja8eoa53cbfq.jpg',
            alt: 'Ботинки мужские KELTON',
            price: { old: '18 990 руб.', current: '11 394 руб.' },
            brand: 'KELTON',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [40, 41, 42, 43],
            is_discount: { active: true, value: 40 },
        },
        {
            id: 'prod211',
            title: 'Ботинки мужские ARA',
            url: '/category/muzhskaya-obuv/botinki_muzhskie_prod211/',
            image: '/upload/resize_cache/iblock/649/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/hktrx1ag4ldmxx8pufm5i2997wcsbell.jpg',
            alt: 'Ботинки мужские ARA',
            price: { old: '17 950 руб.', current: '14 360 руб.' },
            brand: 'ARA',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [41, 42, 43, 44, 45],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod212',
            title: 'Полуботинки мужские CAPRICE',
            url: '/category/muzhskaya-obuv/polubotinki_muzhskie_prod212/',
            image: '/upload/resize_cache/iblock/737/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/nr8qrito4zl43e00l59occwvssgdt9ca.jpg',
            alt: 'Полуботинки мужские CAPRICE',
            price: { old: '21 990 руб.', current: '17 592 руб.' },
            brand: 'CAPRICE',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [40, 41, 42, 43],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod213',
            title: 'Полуботинки мужские RIEKER',
            url: '/category/muzhskaya-obuv/polubotinki_muzhskie_prod213/',
            image: '/upload/resize_cache/iblock/7d8/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/1jphbaxt609rdq375q53zy2ugj4e2ro4.jpg',
            alt: 'Полуботинки мужские RIEKER',
            price: { old: '21 990 руб.', current: '17 592 руб.' },
            brand: 'RIEKER',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [41, 42, 43, 44],
            is_discount: { active: true, value: 20 },
        },
        {
            id: 'prod214',
            title: 'Полуботинки мужские SUAVE',
            url: '/category/muzhskaya-obuv/polubotinki_muzhskie_prod214/',
            image: '/upload/resize_cache/iblock/a7f/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/lc0puw6zc3kd8or21nequz1z83cjhcn0.jpg',
            alt: 'Полуботинки мужские SUAVE',
            price: { old: '16 990 руб.', current: '10 194 руб.' },
            brand: 'SUAVE',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['brown'] },
            sizes: [40, 41, 42, 43],
            is_discount: { active: true, value: 40 },
        },
        {
            id: 'prod215',
            title: 'Полуботинки мужские KELTON',
            url: '/category/muzhskaya-obuv/polubotinki_muzhskie_prod215/',
            image: '/upload/resize_cache/iblock/89f/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/qfoqal188bg3km4a8etu6uk7qr75m5oe.jpg',
            alt: 'Полуботинки мужские KELTON',
            price: { old: '16 990 руб.', current: '10 194 руб.' },
            brand: 'KELTON',
            badges: {
                is_new: { state: false, value: 'NEW' },
                hit: { state: false, value: 'HIT' },
            },
            color: { is_one: true, value: ['black'] },
            sizes: [41, 42, 43, 44],
            is_discount: { active: true, value: 40 },
        },

        // Аксессуары
        {
            id: 'prod408',
            title: 'Зонт складной',
            url: '/category/aksessuary/zonty/skladnye/zont_prod408/',
            image: '/upload/resize_cache/iblock/737/210_210_2c864ec529fb1f49b0f3d35348fc0bcf1/nr8qrito4zl43e00l59occwvssgdt9ca.jpg',
            alt: 'Зонт складной',
            price: { current: '1 990 руб.' },
            brand: 'Totes',
            badges: {
                is_new: { state: true, value: 'NEW' },
                hit: { state: true, value: 'HIT' },
            },
            color: { is_one: true, value: ['blue'] },
            sizes: [39, 42, 43],
            is_discount: { active: true, value: 30 },
        },
    ] as Product[],

    // Добавляем фильтры с типизацией
    filter_attr: {
        sizes: [35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45],
        colors: [
            { id: 'black', name: 'Чёрный' },
            { id: 'white', name: 'Белый' },
            { id: 'brown', name: 'Коричневый' },
            { id: 'beige', name: 'Бежевый' },
            { id: 'gray', name: 'Серый' },
            { id: 'blue', name: 'Синий' },
            { id: 'burgundy', name: 'Бордовый' },
            { id: 'red', name: 'Красный' },
            { id: 'pink', name: 'Розовый' },
            { id: 'green', name: 'Зелёный' },
            { id: 'gold', name: 'Золотой' },
            { id: 'silver', name: 'Серебряный' },
            { id: 'multicolor', name: 'Разноцветный' },
        ] as FilterColor[],
        brands: [
            { id: 'ARA', name: 'ARA' },
            { id: 'CAPRICE', name: 'CAPRICE' },
            { id: 'RIEKER', name: 'RIEKER' },
            { id: 'SUAVE', name: 'SUAVE' },
            { id: 'KELTON', name: 'KELTON' },
        ] as FilterBrand[],
        specials: [
            { id: 'is_new', name: 'Новинки', type: 'badge' as const },
            { id: 'is_hit', name: 'Хиты', type: 'badge' as const },
            { id: 'on_sale', name: 'Со скидкой', type: 'discount' as const },
        ] as FilterSpecial[],
    } as FilterAttributes,

    // Добавляем данные брендов
    brands: [
        { id: '1', name: 'Ara', url: '/category/brendy/ara/', slug: 'ara' },
        {
            id: '2',
            name: 'Atrai',
            url: '/category/brendy/atrai/',
            slug: 'atrai',
        },
        { id: '3', name: 'Axa', url: '/category/brendy/axa/', slug: 'axa' },
        {
            id: '4',
            name: 'Caprice',
            url: '/category/brendy/caprice/',
            slug: 'caprice',
        },
        {
            id: '5',
            name: "D'Torres",
            url: '/category/brendy/d-torres/',
            slug: 'd-torres',
        },
        {
            id: '6',
            name: 'Dino Ricci',
            url: '/category/brendy/dino-ricci/',
            slug: 'dino-ricci',
        },
        {
            id: '7',
            name: 'Fluchos',
            url: '/category/brendy/fluchos/',
            slug: 'fluchos',
        },
        {
            id: '8',
            name: 'Grisport',
            url: '/category/brendy/grisport/',
            slug: 'grisport',
        },
        {
            id: '9',
            name: 'Jomos',
            url: '/category/brendy/jomos/',
            slug: 'jomos',
        },
        {
            id: '10',
            name: 'Josef Seibel',
            url: '/category/brendy/josef-seibel/',
            slug: 'josef-seibel',
        },
        {
            id: '11',
            name: 'Juan Maestre',
            url: '/category/brendy/juan-maestre/',
            slug: 'juan-maestre',
        },
        {
            id: '12',
            name: 'Kelton',
            url: '/category/brendy/kelton/',
            slug: 'kelton',
        },
        {
            id: '13',
            name: 'Luiza Belly',
            url: '/category/brendy/luiza-belly/',
            slug: 'luiza-belly',
        },
        {
            id: '14',
            name: 'Marco Tozzi',
            url: '/category/brendy/marco-tozzi/',
            slug: 'marco-tozzi',
        },
        {
            id: '15',
            name: 'Mia Donna',
            url: '/category/brendy/mia-donna/',
            slug: 'mia-donna',
        },
        {
            id: '16',
            name: 'NexPero',
            url: '/category/brendy/nexpero/',
            slug: 'nexpero',
        },
        {
            id: '17',
            name: 'Peter Kaiser',
            url: '/category/brendy/peter-kaiser/',
            slug: 'peter-kaiser',
        },
        {
            id: '18',
            name: 'Piesanto',
            url: '/category/brendy/piesanto/',
            slug: 'piesanto',
        },
        {
            id: '19',
            name: 'Pitillos',
            url: '/category/brendy/pitillos/',
            slug: 'pitillos',
        },
        {
            id: '20',
            name: 'Remonte',
            url: '/category/brendy/remonte/',
            slug: 'remonte',
        },
        {
            id: '21',
            name: 'Respect',
            url: '/category/brendy/respect/',
            slug: 'respect',
        },
        {
            id: '22',
            name: 'Rieker',
            url: '/category/brendy/rieker/',
            slug: 'rieker',
        },
        {
            id: '23',
            name: 'Romer',
            url: '/category/brendy/romer/',
            slug: 'romer',
        },
        {
            id: '24',
            name: 's.Oliver',
            url: '/category/brendy/s-oliver/',
            slug: 's-oliver',
        },
        {
            id: '25',
            name: 'Semler',
            url: '/category/brendy/semler/',
            slug: 'semler',
        },
        {
            id: '26',
            name: 'Shoiberg',
            url: '/category/brendy/shoiberg/',
            slug: 'shoiberg',
        },
        {
            id: '27',
            name: 'Sioux',
            url: '/category/brendy/sioux/',
            slug: 'sioux',
        },
        { id: '28', name: 'Spur', url: '/category/brendy/spur/', slug: 'spur' },
        {
            id: '29',
            name: 'Suave',
            url: '/category/brendy/suave/',
            slug: 'suave',
        },
        {
            id: '30',
            name: 'Tamaris',
            url: '/category/brendy/tamaris/',
            slug: 'tamaris',
        },
        {
            id: '31',
            name: 'Valley',
            url: '/category/brendy/valley/',
            slug: 'valley',
        },
        {
            id: '32',
            name: 'Waldläufer',
            url: '/category/brendy/waldlaufer/',
            slug: 'waldlaufer',
        },
        {
            id: '33',
            name: 'Wonders',
            url: '/category/brendy/wonders/',
            slug: 'wonders',
        },
    ] as BrandItem[],

    product_categories: [
        // Женская обувь - распределяем по подкатегориям
        { product_id: 'prod101', category_id: 'cat106' }, // Ботинки
        { product_id: 'prod102', category_id: 'cat109' }, // Кроссовки
        { product_id: 'prod103', category_id: 'cat119' }, // Туфли закрытые
        { product_id: 'prod104', category_id: 'cat116' }, // Сапоги
        { product_id: 'prod105', category_id: 'cat104' }, // Босоножки
        { product_id: 'prod106', category_id: 'cat103' }, // Балетки
        { product_id: 'prod107', category_id: 'cat110' }, // Лоферы
        { product_id: 'prod108', category_id: 'cat111' }, // Мокасины
        { product_id: 'prod109', category_id: 'cat112' }, // Полуботинки
        { product_id: 'prod110', category_id: 'cat115' }, // Сандалии
        { product_id: 'prod111', category_id: 'cat105' }, // Ботильоны
        { product_id: 'prod112', category_id: 'cat107' }, // Ботфорты
        { product_id: 'prod113', category_id: 'cat108' }, // Домашняя обувь
        { product_id: 'prod114', category_id: 'cat114' }, // Сабо
        { product_id: 'prod115', category_id: 'cat113' }, // Полусапоги

        // Мужская обувь
        { product_id: 'prod201', category_id: 'cat204' }, // Кроссовки
        { product_id: 'prod202', category_id: 'cat204' }, // Кроссовки
        { product_id: 'prod203', category_id: 'cat207' }, // Полуботинки
        { product_id: 'prod204', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod205', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod206', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod207', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod208', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod209', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod210', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod211', category_id: 'cat203' }, // Ботинки
        { product_id: 'prod212', category_id: 'cat207' }, // Полуботинки
        { product_id: 'prod213', category_id: 'cat207' }, // Полуботинки
        { product_id: 'prod214', category_id: 'cat207' }, // Полуботинки
        { product_id: 'prod215', category_id: 'cat207' }, // Полуботинки

        // Сумки
        { product_id: 'prod301', category_id: 'cat307' }, // Маленькие сумки
        { product_id: 'prod302', category_id: 'cat308' }, // Средние сумки
        { product_id: 'prod303', category_id: 'cat309' }, // Большие сумки
        { product_id: 'prod304', category_id: 'cat310' }, // Кожаные сумки
        { product_id: 'prod305', category_id: 'cat311' }, // Спортивные сумки
        { product_id: 'prod306', category_id: 'cat312' }, // Городские рюкзаки
        { product_id: 'prod307', category_id: 'cat313' }, // Туристические рюкзаки
        { product_id: 'prod308', category_id: 'cat306' }, // Клатчи
        { product_id: 'prod309', category_id: 'cat308' }, // Средние сумки
        { product_id: 'prod310', category_id: 'cat310' }, // Кожаные сумки

        // Аксессуары
        { product_id: 'prod401', category_id: 'cat407' }, // Кожаные ремни
        { product_id: 'prod402', category_id: 'cat408' }, // Тканые ремни
        { product_id: 'prod403', category_id: 'cat409' }, // Мужские кошельки
        { product_id: 'prod404', category_id: 'cat410' }, // Женские кошельки
        { product_id: 'prod405', category_id: 'cat411' }, // Кожаные перчатки
        { product_id: 'prod406', category_id: 'cat412' }, // Трикотажные перчатки
        { product_id: 'prod407', category_id: 'cat413' }, // Автоматические зонты
        { product_id: 'prod408', category_id: 'cat414' }, // Складные зонты
        { product_id: 'prod409', category_id: 'cat407' }, // Кожаные ремни
        { product_id: 'prod410', category_id: 'cat409' }, // Мужские кошельки

        // Специальные категории (некоторые товары в "ЛУЧШАЯ ЦЕНА" и "НОВИНКИ")
        { product_id: 'prod101', category_id: 'cat101' }, // Ботинки в ЛУЧШАЯ ЦЕНА
        { product_id: 'prod103', category_id: 'cat102' }, // Туфли в НОВИНКИ
        { product_id: 'prod201', category_id: 'cat201' }, // Кроссовки в ЛУЧШАЯ ЦЕНА
        { product_id: 'prod203', category_id: 'cat201' }, // Полуботинки в ЛУЧШАЯ ЦЕНА
        { product_id: 'prod301', category_id: 'cat301' }, // Сумка в ЛУЧШАЯ ЦЕНА
        { product_id: 'prod401', category_id: 'cat401' }, // Ремень в ЛУЧШАЯ ЦЕНА
    ] as ProductCategory[],

    // Хлебные крошки для основных страниц
    breadcrumbs: {
        home: { label: 'Главная', href: '/' },
        categories: { label: 'Категории', href: '/category' },
        brands: { label: 'Бренды', href: '/category/brendy' },
    },

    // Индексы
    indexes: {
        categories_by_path: {} as Record<string, Category>,
        products_by_id: {} as Record<string, Product>,
        products_by_url: {} as Record<string, Product>,
        brands_by_slug: {} as Record<string, BrandItem>,
    },

    init() {
        // Инициализация индексов категорий и продуктов
        this.categories.forEach((category) => {
            this.indexes.categories_by_path[category.path] = category;
        });
        this.products.forEach((product) => {
            this.indexes.products_by_id[product.id] = product;
            this.indexes.products_by_url[product.url] = product;
        });
        // Инициализация индекса брендов
        this.brands.forEach((brand) => {
            this.indexes.brands_by_slug[brand.slug] = brand;
        });
    },
};

database.init();

// === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

function findCategoryByPath(path: string): Category | undefined {
    return database.indexes.categories_by_path[path];
}

function getProductById(productId: string): Product | undefined {
    return database.indexes.products_by_id[productId];
}

function getBrandBySlug(slug: string): BrandItem | undefined {
    return database.indexes.brands_by_slug[slug];
}

function getSubcategories(parentId: string | null): Category[] {
    return database.categories
        .filter((c) => c.parent_id === parentId)
        .sort((a, b) => a.sort_order - b.sort_order);
}

function hasSubcategories(categoryId: string): boolean {
    return database.categories.some((c) => c.parent_id === categoryId);
}

function getAllDescendantCategoryIds(categoryId: string): string[] {
    const result: string[] = [categoryId];

    function findChildren(parentId: string) {
        const children = database.categories.filter(
            (c) => c.parent_id === parentId,
        );
        for (const child of children) {
            result.push(child.id);
            findChildren(child.id);
        }
    }

    findChildren(categoryId);
    return result;
}

function getBreadcrumbsFromPath(path: string): BreadcrumbItem[] {
    const segments = path.split('/').filter((segment) => segment.trim() !== '');
    const breadcrumbs: BreadcrumbItem[] = [
        { label: 'Главная', href: '/' },
        { label: 'Категории', href: '/category' },
    ];

    let currentPath = '';
    for (const segment of segments) {
        currentPath = currentPath ? `${currentPath}/${segment}` : segment;
        const category = findCategoryByPath(currentPath);

        if (category) {
            const subcategories = getSubcategories(category.id);
            breadcrumbs.push({
                label: category.name,
                href: `/category/${currentPath}`,
                title: category.name,
                subcategories:
                    subcategories.length > 0
                        ? Object.fromEntries(
                              subcategories.map((sub) => [
                                  sub.slug,
                                  {
                                      label: sub.name,
                                      href: `/category/${sub.path}`,
                                      title: sub.name,
                                  },
                              ]),
                          )
                        : undefined,
            });
        } else {
            breadcrumbs.push({
                label: segment,
                href: `/category/${currentPath}`,
                title: segment,
            });
        }
    }

    return breadcrumbs;
}

function getProductsByCategoryPath(
    categoryPath: string,
    includeChildren: boolean = true,
): Product[] {
    const category = findCategoryByPath(categoryPath);
    if (!category) return [];

    const categoryIds = includeChildren
        ? getAllDescendantCategoryIds(category.id)
        : [category.id];

    const productIds = database.product_categories
        .filter((pc) => categoryIds.includes(pc.category_id))
        .map((pc) => pc.product_id);

    const uniqueProductIds = [...new Set(productIds)];
    return uniqueProductIds
        .map((id) => getProductById(id))
        .filter(Boolean) as Product[];
}

function getProductCategories(productId: string): Category[] {
    const categoryIds = database.product_categories
        .filter((pc) => pc.product_id === productId)
        .map((pc) => pc.category_id);

    return categoryIds
        .map((id) => database.categories.find((c) => c.id === id))
        .filter(Boolean) as Category[];
}

// === ФУНКЦИИ ДЛЯ РАБОТЫ С БРЕНДАМИ ===

export function getAllBrands(): BrandItem[] {
    return database.brands;
}

// data.ts

export function getBrandsData(): BrandsDataResult {
    return {
        brands: database.brands,
        breadcrumbs: [
            database.breadcrumbs.home,
            database.breadcrumbs.categories,
            database.breadcrumbs.brands,
        ],
    };
}

export function getBrandData(
    brandSlug: string,
    currentPage: number = 1,
): BrandDataResult {
    const brand = getBrandBySlug(brandSlug);

    const baseBreadcrumbs: BreadcrumbItem[] = [
        database.breadcrumbs.home,
        database.breadcrumbs.categories,
        database.breadcrumbs.brands,
    ];

    if (!brand) {
        return {
            brand: brandSlug,
            products: [],
            breadcrumbs: [
                ...baseBreadcrumbs,
                { label: brandSlug, href: `/category/brendy/${brandSlug}` },
            ],
            currentPage,
        };
    }

    const products = database.products.filter(
        (product) => product.brand.toLowerCase() === brand.name.toLowerCase(),
    );

    const breadcrumbs: BreadcrumbItem[] = [
        ...baseBreadcrumbs,
        {
            label: brand.name,
            href: `/category/brendy/${brandSlug}`,
            title: brand.name,
        },
    ];

    return {
        brand: brand.name,
        products,
        breadcrumbs,
        currentPage,
    };
}

// === ОСНОВНЫЕ ЭКСПОРТИРУЕМЫЕ ФУНКЦИИ ===

export function getProductData(segments: string[]): ProductDataResult {
    if (segments.length === 0)
        return { isProduct: false, product: null, breadcrumbs: [] };

    const fullPath = `/category/${segments.join('/')}/`;
    const product = database.indexes.products_by_url[fullPath];

    if (product) {
        const productCats = getProductCategories(product.id);
        const mainCategory = productCats[0];
        const breadcrumbs = mainCategory
            ? getBreadcrumbsFromPath(mainCategory.path)
            : [];

        return {
            isProduct: true,
            product,
            breadcrumbs,
        };
    }

    return { isProduct: false, product: null, breadcrumbs: [] };
}

export function getCategoryData(
    path: string,
    currentPage: number = 1,
): CategoryDataResult {
    const category = findCategoryByPath(path);

    if (!category) {
        return { category: null, products: [], breadcrumbs: [], currentPage };
    }

    const includeChildren = hasSubcategories(category.id);
    const products = getProductsByCategoryPath(path, includeChildren);
    const breadcrumbs = getBreadcrumbsFromPath(path);

    return {
        category,
        products,
        breadcrumbs,
        currentPage,
    };
}

export function filterProducts(
    filters: FilterParams,
    productsToFilter?: Product[],
): Product[] {
    console.log('FILTERS:', filters);

    const products = productsToFilter || database.products;

    return products.filter((product) => {
        const {
            query,
            sizes,
            colors,
            brands,
            minPrice,
            maxPrice,
            onSale,
            isNew,
            isHit,
        } = filters;

        const toBoolean = (
            value: boolean | string | undefined,
        ): boolean | undefined => {
            if (value === undefined) return undefined;
            if (typeof value === 'boolean') return value;
            return value === 'true';
        };

        const isNewBool = toBoolean(isNew);
        const isHitBool = toBoolean(isHit);
        const onSaleBool = toBoolean(onSale);

        const productPrice = parsePrice(product.price.current);

        const result =
            (!query?.trim() ||
                product.title
                    .toLowerCase()
                    .includes(query.toLowerCase().trim())) &&
            (!sizes?.length ||
                sizes.some((size) => product.sizes.includes(parseInt(size)))) &&
            (!colors?.length ||
                colors.some((color) =>
                    (product.color.is_one
                        ? [product.color.value[0]]
                        : product.color.value
                    ).includes(color),
                )) &&
            (!brands?.length || brands.includes(product.brand)) &&
            (minPrice === undefined || productPrice >= minPrice) &&
            (maxPrice === undefined || productPrice <= maxPrice) &&
            (onSaleBool === undefined ||
                onSaleBool === product.is_discount.active) &&
            (isNewBool === undefined ||
                isNewBool === product.badges.is_new.state) &&
            (isHitBool === undefined || isHitBool === product.badges.hit.state);

        return result;
    });
}

// Функция для парсинга цены
function parsePrice(priceString: string): number {
    return parseInt(priceString.replace(/\D/g, '')) || 0;
}

// Функция для получения активных бейджей
export function getActiveBadges(product: Product): string[] {
    const activeBadges: string[] = [];

    if (product.badges.is_new.state) {
        activeBadges.push(product.badges.is_new.value);
    }

    if (product.badges.hit.state) {
        activeBadges.push(product.badges.hit.value);
    }

    if (product.is_discount.active) {
        activeBadges.push(`-${product.is_discount.value}%`);
    }

    return activeBadges;
}

// Старая функция для обратной совместимости
export function searchProducts(query: string): Product[] {
    return filterProducts({ query });
}

// Функция для определения типа роута по сегментам пути
export function getRouteType(
    segments: string[],
): 'category' | 'brand' | 'product' {
    if (segments.length === 0) return 'category';

    if (segments[0] === 'brendy') {
        return segments.length > 1 ? 'brand' : 'category';
    }

    const fullPath = `/category/${segments.join('/')}/`;
    if (database.indexes.products_by_url[fullPath]) {
        return 'product';
    }

    return 'category';
}

// Функция для получения хлебных крошек в зависимости от типа роута
export function getBreadcrumbsByRouteType(
    segments: string[],
    routeType: 'category' | 'brand' | 'product',
): BreadcrumbItem[] {
    switch (routeType) {
        case 'brand':
            if (segments.length >= 2) {
                const brandSlug = segments[1];
                const brandData = getBrandData(brandSlug);
                return brandData.breadcrumbs && brandData.breadcrumbs.length > 0
                    ? brandData.breadcrumbs
                    : [
                          database.breadcrumbs.home,
                          database.breadcrumbs.categories,
                          database.breadcrumbs.brands,
                          {
                              label: brandSlug,
                              href: `/category/brendy/${brandSlug}`,
                          },
                      ];
            }
            break;

        case 'product':
            const productData = getProductData(segments);
            return productData.breadcrumbs && productData.breadcrumbs.length > 0
                ? productData.breadcrumbs
                : [
                      database.breadcrumbs.home,
                      database.breadcrumbs.categories,
                      {
                          label: 'Товар',
                          href: `/category/${segments.join('/')}`,
                      },
                  ];

        case 'category':
        default:
            if (segments[0] === 'brendy' && segments.length === 1) {
                return [
                    database.breadcrumbs.home,
                    database.breadcrumbs.categories,
                    database.breadcrumbs.brands,
                ];
            }

            const categoryBreadcrumbs = getBreadcrumbsFromPath(
                segments.join('/'),
            );
            return categoryBreadcrumbs && categoryBreadcrumbs.length > 0
                ? categoryBreadcrumbs
                : [
                      database.breadcrumbs.home,
                      database.breadcrumbs.categories,
                      {
                          label: segments[segments.length - 1] || 'Категория',
                          href: `/category/${segments.join('/')}`,
                      },
                  ];
    }

    return [database.breadcrumbs.home, database.breadcrumbs.categories];
}

// === ФУНКЦИИ ДЛЯ ФИЛЬТРОВ ===

export function getFilterSections(): FilterSection[] {
    const { sizes, colors, brands, specials } = database.filter_attr;

    const prices = database.products.map(
        (product) => parseInt(product.price.current.replace(/\D/g, '')) || 0,
    );
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);

    return [
        {
            id: 'special' as const,
            title: 'Особые',
            isOpen: true,
            options: specials.map((special) => ({
                id: special.id,
                label: special.name,
                type: 'checkbox' as const,
            })),
        },
        {
            id: 'price' as const,
            title: 'Цена, руб.',
            isOpen: true,
            options: [
                {
                    id: 'on_sale',
                    label: 'Только товары со скидкой',
                    type: 'checkbox' as const,
                },
            ],
            priceRange: {
                min: minPrice,
                max: maxPrice,
            },
        },
        {
            id: 'size' as const,
            title: 'Размер',
            isOpen: false,
            options: sizes.map((size) => ({
                id: size.toString(),
                label: size.toString(),
                type: 'size' as const,
            })),
        },
        {
            id: 'color' as const,
            title: 'Цвет',
            isOpen: false,
            options: colors.map((color) => ({
                id: color.id,
                label: color.name,
                type: 'checkbox' as const,
            })),
        },
        {
            id: 'brand' as const,
            title: 'Бренд',
            isOpen: false,
            options: brands.map((brand) => ({
                id: brand.id,
                label: brand.name,
                type: 'checkbox' as const,
            })),
        },
    ];
}
