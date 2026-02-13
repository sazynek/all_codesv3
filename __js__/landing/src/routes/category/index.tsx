import { createFileRoute } from '@tanstack/react-router';
import { CategoryPage } from '../../components/CategoryPage';

export const Route = createFileRoute('/category/')({
    component: CategoryPage,
    validateSearch: (search: Record<string, unknown>) => {
        return {
            q: (search.q as string) || '',
            pag: Number(search.pag) || 1,
        };
    },
});
