// src/routes/__root.tsx
import { Outlet, createRootRoute } from '@tanstack/react-router';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';

export const Route = createRootRoute({
    component: App,
});

function App() {
    return (
        <div className='pt-4'>
            <Header />
            <Outlet />
            <Footer />
        </div>
    );
}
`  `;
