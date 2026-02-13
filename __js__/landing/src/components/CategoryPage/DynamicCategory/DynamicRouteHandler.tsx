// src/components/DynamicRouteHandler/DynamicRouteHandler.tsx
import { useNavigate } from '@tanstack/react-router';
import {
    filterProducts,
    getBrandData,
    getBreadcrumbsByRouteType,
    getCategoryData,
    getProductData,
    getRouteType,
} from '../../../data';
import { ProductDynamicDetailPage } from './ProductDynamicDetailPage';
import { CategoryDynamicPage } from './CategoryDynamicPage';
import { Breadcrumbs } from '../../ui/Breadcrumbs';

interface DynamicRouteHandlerProps {
    segments: string[];
    searchParams: any;
    onSearchParamsChange: (params: any) => void;
}

export function DynamicRouteHandler({
    segments,
    searchParams,
    onSearchParamsChange,
}: DynamicRouteHandlerProps) {
    const navigate = useNavigate();

    console.log('SEARCH PARAMS ', searchParams);
    console.log('SEGMENTS ', segments);
    console.log('ROUTE TYPE ', getRouteType(segments));

    const handlePageChange = (page: number) => {
        onSearchParamsChange({ ...searchParams, pag: page });
    };

    const handleResetFilters = () => {
        onSearchParamsChange({ pag: 1 });
    };

    // Функция для возврата назад
    const handleGoBack = () => {
        navigate({ to: '..' }); // Возврат на предыдущую страницу
    };

    // Функция для возврата на главную
    const handleGoHome = () => {
        navigate({ to: '/' });
    };

    // Определяем тип роута
    const routeType = getRouteType(segments);

    // Обработка страницы товара (одинаково для всех типов роутов)
    if (routeType === 'product') {
        const { isProduct, product, breadcrumbs } = getProductData(segments);
        if (isProduct && product) {
            return (
                <ProductDynamicDetailPage
                    product={product}
                    breadcrumbItems={breadcrumbs}
                />
            );
        }
    }

    // Обработка страницы бренда
    if (routeType === 'brand' && segments.length >= 2) {
        const brandSlug = segments[1];
        const brandData = getBrandData(brandSlug);

        if (brandData.products.length > 0) {
            const filteredProducts = filterProducts(
                {
                    query: searchParams.q,
                    sizes: searchParams.sizes
                        ? searchParams.sizes.split(',')
                        : undefined,
                    colors: searchParams.colors
                        ? searchParams.colors.split(',')
                        : undefined,
                    brands: searchParams.brands
                        ? searchParams.brands.split(',')
                        : undefined,
                    minPrice: searchParams.minPrice,
                    maxPrice: searchParams.maxPrice,
                    onSale: searchParams.onSale,
                    isNew: searchParams.isNew,
                    isHit: searchParams.isHit,
                },
                brandData.products,
            );

            console.log('FILTERED_BRAND_PRODUCTS: ', filteredProducts);

            return (
                <CategoryDynamicPage
                    products={filteredProducts}
                    breadcrumbItems={brandData.breadcrumbs}
                    currentPage={searchParams.pag}
                    onPageChange={handlePageChange}
                    onResetFilters={handleResetFilters}
                    searchParams={searchParams}
                    isSearchResults={!!searchParams.q}
                    searchQuery={searchParams.q}
                    categoryPath={segments.join('/')}
                    isBrandPage={true}
                    brandName={brandData.brand}
                />
            );
        }

        // Бренд не найден
        const breadcrumbs = getBreadcrumbsByRouteType(segments, routeType);

        return (
            <div className='container mx-auto px-4 py-8'>
                <Breadcrumbs items={breadcrumbs} />
                <div className='text-center py-12'>
                    <h1 className='text-2xl font-bold text-gray-900 mb-4'>
                        Бренд не найден
                    </h1>
                    <p className='text-lg text-gray-600 mb-8'>
                        К сожалению, бренд "{brandSlug}" не существует или был
                        удален.
                    </p>
                    <div className='flex flex-col sm:flex-row gap-4 justify-center'>
                        <button
                            onClick={handleGoBack}
                            className='px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium'
                        >
                            ← Вернуться назад
                        </button>
                        <button
                            onClick={handleGoHome}
                            className='px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 font-medium'
                        >
                            На главную страницу
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Обработка категорий (включая индекс брендов)
    const categoryData = getCategoryData(segments.join('/'));
    console.log('CATEGORY_DATA: ', categoryData);

    if (categoryData.category) {
        const categoryProducts = categoryData.products;

        const filteredProducts = filterProducts(
            {
                query: searchParams.q,
                sizes: searchParams.sizes
                    ? searchParams.sizes.split(',')
                    : undefined,
                colors: searchParams.colors
                    ? searchParams.colors.split(',')
                    : undefined,
                brands: searchParams.brands
                    ? searchParams.brands.split(',')
                    : undefined,
                minPrice: searchParams.minPrice,
                maxPrice: searchParams.maxPrice,
                onSale: searchParams.onSale,
                isNew: searchParams.isNew,
                isHit: searchParams.isHit,
            },
            categoryProducts,
        );

        console.log('FILTERED_PRODUCTS: ', filteredProducts);

        return (
            <CategoryDynamicPage
                products={filteredProducts}
                breadcrumbItems={categoryData.breadcrumbs}
                currentPage={searchParams.pag}
                onPageChange={handlePageChange}
                onResetFilters={handleResetFilters}
                searchParams={searchParams}
                isSearchResults={!!searchParams.q}
                searchQuery={searchParams.q}
                categoryPath={segments.join('/')}
                isBrandPage={segments[0] === 'brendy' && segments.length === 1}
            />
        );
    }

    // Категория/бренд не найдены
    const breadcrumbs = getBreadcrumbsByRouteType(segments, routeType);

    // Получаем имя категории/бренда для сообщения
    const entityName = segments.length > 0 ? segments[segments.length - 1] : '';

    return (
        <div className='container mx-auto px-4 py-8'>
            <Breadcrumbs items={breadcrumbs} />
            <div className='text-center py-12'>
                <h1 className='text-2xl font-bold text-gray-900 mb-4'>
                    {routeType === 'brand'
                        ? 'Бренд не найден'
                        : 'Категория не найдена'}
                </h1>
                <p className='text-lg text-gray-600 mb-8'>
                    {routeType === 'brand'
                        ? `К сожалению, бренд "${entityName}" не существует или был удален.`
                        : `К сожалению, категория "${entityName}" не существует или была удалена.`}
                </p>
                <div className='flex flex-col sm:flex-row gap-4 justify-center'>
                    <button
                        onClick={handleGoBack}
                        className='px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium'
                    >
                        ← Вернуться назад
                    </button>
                    <button
                        // @ts-ignore
                        onClick={() => navigate({ to: '/category' })}
                        className='px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 font-medium'
                    >
                        Все категории
                    </button>
                    <button
                        onClick={handleGoHome}
                        className='px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 font-medium'
                    >
                        На главную страницу
                    </button>
                </div>
            </div>
        </div>
    );
}
