import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation } from 'swiper/modules';

// @ts-ignore
// import 'swiper/css';
// @ts-ignore
// import 'swiper/css/navigation';
import { Card } from './Card';
import type { ProductsSliderProps } from '../../../types';

// Основной компонент слайдера
export const ProductsSlider = ({ products, onSwiper }: ProductsSliderProps) => {
    return (
        <div className='info__content content-info container'>
            <div className='content-info__list'>
                <div className='content-info__item active'>
                    <div className='products products--type-2'>
                        <Swiper
                            onSwiper={onSwiper}
                            modules={[Navigation]}
                            spaceBetween={20}
                            slidesPerView={4}
                            navigation={{
                                prevEl: '.products-swiper-prev',
                                nextEl: '.products-swiper-next',
                            }}
                            breakpoints={{
                                320: {
                                    slidesPerView: 1,
                                    spaceBetween: 10,
                                },
                                640: {
                                    slidesPerView: 2,
                                    spaceBetween: 15,
                                },
                                1024: {
                                    slidesPerView: 3,
                                    spaceBetween: 20,
                                },
                                1280: {
                                    slidesPerView: 4,
                                    spaceBetween: 20,
                                },
                            }}
                            className='products__list'
                        >
                            {products.map((product) => (
                                <SwiperSlide
                                    key={product.id}
                                    className='flex justify-center'
                                >
                                    <Card product={product} />
                                </SwiperSlide>
                            ))}
                        </Swiper>
                    </div>
                </div>
            </div>
        </div>
    );
};
