// src/routes/category/brendy/$.tsx
import { createFileRoute } from '@tanstack/react-router';
import { DynamicRouteHandler } from '../../../components/CategoryPage/DynamicCategory/DynamicRouteHandler';

export const Route = createFileRoute('/category/brendy/$')({
    component: BrandAnyPage,
    validateSearch: (hook_search: Record<string, unknown>) => {
        const cleanSearch: any = { pag: Number(hook_search.pag) || 1 };

        // Добавляем только непустые параметры
        if (hook_search.q && String(hook_search.q).trim())
            cleanSearch.q = String(hook_search.q);
        if (hook_search.sizes && String(hook_search.sizes).trim())
            cleanSearch.sizes = String(hook_search.sizes);
        if (hook_search.colors && String(hook_search.colors).trim())
            cleanSearch.colors = String(hook_search.colors);
        if (hook_search.brands && String(hook_search.brands).trim())
            cleanSearch.brands = String(hook_search.brands);
        if (hook_search.minPrice)
            cleanSearch.minPrice = Number(hook_search.minPrice);
        if (hook_search.maxPrice)
            cleanSearch.maxPrice = Number(hook_search.maxPrice);
        if (hook_search.onSale === 'true') cleanSearch.onSale = 'true';
        if (hook_search.isNew === 'true') cleanSearch.isNew = 'true';
        if (hook_search.isHit === 'true') cleanSearch.isHit = 'true';

        return cleanSearch;
    },
});

function BrandAnyPage() {
    const { _splat } = Route.useParams();
    const hook_search = Route.useSearch();
    const navigate = Route.useNavigate();

    // Для брендов добавляем префикс "brendy" к сегментам
    const brandSegment = _splat || '';
    const segments = brandSegment
        ? ['brendy', ...brandSegment.split('/').filter(Boolean)]
        : ['brendy'];

    const handleSearchParamsChange = (newParams: any) => {
        navigate({ search: newParams });
    };

    return (
        <DynamicRouteHandler
            segments={segments}
            searchParams={hook_search}
            onSearchParamsChange={handleSearchParamsChange}
        />
    );
}
