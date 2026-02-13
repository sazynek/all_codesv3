import { Swiper as SwiperType } from 'swiper';
// Тип для бренда в списке брендов
export interface BrandItem {
    id: string;
    name: string;
    url: string;
    slug: string;
}

// Тип для результата данных бренда
export interface BrandDataResult {
    brand: string;
    products: Product[];
    breadcrumbs: BreadcrumbItem[];
    currentPage: number;
}

// Тип для результата данных списка брендов
export interface BrandsDataResult {
    brands: BrandItem[];
    breadcrumbs: BreadcrumbItem[];
}
// Основные типы данных
export interface Product {
    id: string;
    title: string;
    url: string;
    image: string;
    alt: string;
    price: {
        current: string;
        old?: string;
    };
    brand: string;
    badges: {
        is_new: {
            state: boolean;
            value: string;
        };
        hit: {
            state: boolean;
            value: string;
        };
    };
    color: {
        is_one: boolean;
        value: string[];
    };
    sizes: number[];
    is_discount: {
        active: boolean;
        value: number;
    };
}

export interface Category {
    id: string;
    name: string;
    slug: string;
    parent_id: string | null;
    path: string;
    level: number;
    sort_order: number;
    is_special?: boolean;
}

export interface ProductCategory {
    product_id: string;
    category_id: string;
}

export interface BreadcrumbItem {
    label: string;
    href?: string;
    title?: string;
    icon?: React.ReactNode;
    subcategories?: Record<string, BreadcrumbItem>;
    special?: boolean;
    isCurrent?: boolean;
}

// Типы для фильтров
export interface FilterColor {
    id: string;
    name: string;
}

export interface FilterBrand {
    id: string;
    name: string;
}

export interface FilterSpecial {
    id: string;
    name: string;
    type: 'badge' | 'discount';
}

export interface FilterAttributes {
    sizes: number[];
    colors: FilterColor[];
    brands: FilterBrand[];
    specials: FilterSpecial[];
}

export interface PriceRange {
    min: number;
    max: number;
}

// Типы для компонентов фильтров
export interface FilterOption {
    id: string;
    label: string;
    type: 'checkbox' | 'size' | 'price';
}

export interface FilterSection {
    id: 'special' | 'price' | 'size' | 'color' | 'brand';
    title: string;
    isOpen: boolean;
    options: FilterOption[];
    priceRange?: PriceRange;
}

export interface FilterParams {
    query?: string;
    sizes?: string[];
    colors?: string[];
    brands?: string[];
    minPrice?: number;
    maxPrice?: number;
    onSale?: boolean | string;
    isNew?: boolean | string;
    isHit?: boolean | string;
}

// types.ts
export interface FilterPropsType {
    className?: string;
    searchParams?: any;
    isBrandPage?: boolean; // Добавляем новый пропс
}
// Типы для компонентов UI
export interface ProductCardProps {
    product: Product;
}

export interface ProductsSliderProps {
    products: Product[];
    onSwiper: (swiper: SwiperType) => void;
}

export interface NavItem {
    id: string;
    title: string;
    isActive?: boolean;
}

export interface InfoNavProps {
    activeCategory: string;
    onCategoryChange: (categoryId: string) => void;
    onNext: () => void;
    onPrev: () => void;
}

export interface CategoryItem {
    id: string;
    title: string;
    url: string;
    image: string;
    alt: string;
    className?: string;
    background: string;
}

// types.ts

// Тип для элемента подменю
export interface SubMenuItem {
    id: string;
    title: string;
    url: string;
    is_special?: boolean; // Добавляем is_special как опциональное свойство
}

// Основной тип для пункта меню
export interface MenuItem {
    id: string;
    title: string;
    url?: string;
    submenu?: SubMenuItem[]; // Используем новый тип для подменю
    is_special?: boolean; // Делаем опциональным для основного пункта меню
}

// Типы для компонента Range Slider
export interface PriceRangeSliderProps {
    min: number;
    max: number;
    onChange: (min: number, max: number) => void;
    currentMin?: number;
    currentMax?: number;
}

// Типы для компонента FilterSectionAccordion
export interface FilterSectionAccordionProps {
    section: FilterSection;
    onOptionChange: (
        sectionId: string,
        optionId: string,
        value: boolean | number,
    ) => void;
    currentFilters: FilterParams;
}

// Типы для функций базы данных
export interface Database {
    categories: Category[];
    products: Product[];
    filter_attr: FilterAttributes;
    product_categories: ProductCategory[];
    indexes: {
        categories_by_path: Record<string, Category>;
        products_by_id: Record<string, Product>;
        products_by_url: Record<string, Product>;
    };
    init: () => void;
}

// Типы для результатов функций
export interface ProductDataResult {
    isProduct: boolean;
    product: Product | null;
    breadcrumbs: BreadcrumbItem[];
}

export interface CategoryDataResult {
    category: Category | null;
    products: Product[];
    breadcrumbs: BreadcrumbItem[];
    currentPage: number;
}

// Типы для хуков навигации
export interface SearchParams {
    pag?: number;
    q?: string;
    sizes?: string;
    colors?: string;
    brands?: string;
    minPrice?: number;
    maxPrice?: number;
    onSale?: string;
    isNew?: string;
    isHit?: string;
}
