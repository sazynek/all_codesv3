import { useRef, useState } from 'react';
import { ProductsSlider } from './ProductsSlider';
import { InfoNav } from './InfoNav';
import { Swiper as SwiperType } from 'swiper';
import type { Product } from '../../../types';
import { database } from '../../../data';

export const ProductComp = () => {
    const swiperRef = useRef<SwiperType>(null);
    const [activeCategory, setActiveCategory] = useState('1');

    // Берем товары из нашей database
    const categoryProducts: Record<string, Product[]> = {
        '1': [
            // Популярные товары - берем первые 6 товаров из женской обуви
            database.products[0], // prod101 - Ботинки женские кожаные ARA
            database.products[1], // prod102 - Кроссовки женские спортивные
            database.products[2], // prod103 - Туфли женские закрытые
            database.products[3], // prod104 - Сапоги женские зимние
            database.products[4], // prod105 - Босоножки женские летние
            database.products[5], // prod106 - Балетки женские классические
        ],
        '2': [
            // Новинки - берем товары с бейджами NEW
            database.products[0], // prod101 - NEW, -20%
            database.products[2], // prod103 - NEW
            database.products[6], // prod107 - Лоферы женские кожаные - NEW
            database.products[10], // prod111 - Ботильоны женские замшевые - NEW
            database.products[14], // prod115 - Полусапоги женские демисезонные - NEW
            database.products[15], // prod201 - Кроссовки мужские TAMARIS - NEW
        ],
        '3': [
            // Распродажа - берем товары со скидками
            database.products[1], // prod102 - -23%
            database.products[5], // prod106 - -25%
            database.products[7], // prod108 - -25%
            database.products[9], // prod110 - -30%
            database.products[11], // prod112 - -20%
            database.products[13], // prod114 - -20%
        ],
    };

    const handleNext = () => {
        swiperRef.current?.slideNext();
    };

    const handlePrev = () => {
        swiperRef.current?.slidePrev();
    };

    const handleCategoryChange = (categoryId: string) => {
        setActiveCategory(categoryId);
        // Сбрасываем слайдер на первый слайд при смене категории
        swiperRef.current?.slideTo(0);
    };

    return (
        <section about='products' className='mt-10'>
            <InfoNav
                activeCategory={activeCategory}
                onCategoryChange={handleCategoryChange}
                onNext={handleNext}
                onPrev={handlePrev}
            />
            <ProductsSlider
                products={categoryProducts[activeCategory]}
                onSwiper={(swiper: SwiperType | null) =>
                    (swiperRef.current = swiper)
                }
            />
        </section>
    );
};
