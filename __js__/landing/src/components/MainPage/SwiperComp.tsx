import { Swiper, SwiperSlide } from 'swiper/react';
import { Autoplay, EffectFade } from 'swiper/modules';
// @ts-ignore
// import 'swiper/css';
// // @ts-ignore
// import 'swiper/css/pagination';
// // @ts-ignore
// import 'swiper/css/effect-fade';
// // @ts-ignore

// import 'swiper/css/navigation';
import { useRef, useState } from 'react';

export const HeroSlider = () => {
    const slides = [
        {
            id: 1,
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/b3b/975_500_2c864ec529fb1f49b0f3d35348fc0bcf1/p3gjd5rwb5ylbsy13r6b54h22aqkl9tb.jpg',
            alt: 'тамарис',
            remark: 'с 24 по 31 октября',
            title: ['до -40% на обувь', 'бренда Tamaris!'],
            subtitle: 'в интернет-магазине и в сети салонов',
            buttonText: 'подробнее',
            buttonLink: 'https://example.com/promos/dni-brenda-tamaris2/',
        },
        {
            id: 2,
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/ce6/975_500_2c864ec529fb1f49b0f3d35348fc0bcf1/l9u1dcrt18uivddnjg3he28zvz8l4h42.jpg',
            alt: 'Специальное предложение',
            remark: 'скидки',
            title: ['до - 31% ⚡', 'на новинки сезона!'],
            subtitle: 'в интернет-магазине',
            buttonText: 'выбрать',
            buttonLink: 'https://example.com/catalog/zhenskaya-obuv/',
        },
        {
            id: 3,
            image: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/71f/975_500_2c864ec529fb1f49b0f3d35348fc0bcf1/hka3dh8m755s1oeeo691c2typxpcayzn.jpg',
            alt: 'Новая коллекция',
            remark: 'НОВИНКИ!',
            title: ['Коллекция', 'Осень-Зима 25/26'],
            subtitle: 'в интернет-магазине и в сети салонов',
            buttonText: 'смотреть',
            buttonLink: 'https://example.com/catalog/zhenskaya-obuv/new/',
        },
    ];
    const swiperRef = useRef<any | null>(null);
    const [activeIndex, setActiveIndex] = useState(0);

    return (
        <section className='slider w-full pt-5'>
            <Swiper
                modules={[EffectFade, Autoplay]}
                spaceBetween={0}
                slidesPerView={1}
                effect='fade'
                fadeEffect={{ crossFade: true }}
                speed={600}
                autoplay={{
                    delay: 5000,
                    disableOnInteraction: false,
                }}
                onSwiper={(swiper) => {
                    swiperRef.current = swiper;
                }}
                onSlideChange={(swiper) => {
                    setActiveIndex(swiper.activeIndex);
                }}
                className='slider__list'
            >
                {slides.map((slide, _index) => (
                    <SwiperSlide key={slide.id} className='slider__item'>
                        <div className='slider__row flex min-h-[500px]'>
                            <div className='slider__col slider__col--image w-1/2'>
                                <div className='slider__image h-full'>
                                    <img
                                        src={slide.image}
                                        alt={slide.alt}
                                        className='w-full h-full object-cover'
                                    />
                                </div>
                            </div>

                            <div className='slider__col slider__col--content w-1/2 flex flex-col justify-center p-12 bg-gray-50'>
                                <div className='slider__content mb-8 text-start'>
                                    <div className='slider__remark text-lg text-gray-600 mb-4'>
                                        {slide.remark}
                                    </div>
                                    <div className='slider__title font-raleway mb-4'>
                                        {slide.title.map((line, idx) => (
                                            <span
                                                key={idx}
                                                className='text-3xl block'
                                            >
                                                {line}
                                            </span>
                                        ))}
                                    </div>
                                    <div className='slider__remark text-lg text-gray-600'>
                                        {slide.subtitle}
                                    </div>
                                </div>

                                <div className='slider__btn flex items-center gap-6 justify-start'>
                                    <a
                                        href={slide.buttonLink}
                                        className='btn bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg transition-colors duration-200 inline-block'
                                    >
                                        {slide.buttonText}
                                    </a>

                                    {/* Кастомная пагинация */}
                                    <div className='flex gap-2'>
                                        {slides.map((_, idx) => (
                                            <button
                                                key={idx}
                                                type='button'
                                                className={`w-2.5 h-2.5 rounded-full transition-all duration-300 cursor-pointer ${
                                                    activeIndex === idx
                                                        ? 'bg-blue-600 scale-110'
                                                        : 'bg-gray-300 hover:bg-gray-400'
                                                }`}
                                                onClick={() => {
                                                    swiperRef.current?.slideTo(
                                                        idx,
                                                    );
                                                }}
                                                aria-label={`Перейти к слайду ${
                                                    idx + 1
                                                }`}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </SwiperSlide>
                ))}
            </Swiper>
        </section>
    );
};
