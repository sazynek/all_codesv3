import { useRef, useState } from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Autoplay } from 'swiper/modules';
import './swiper-pagination.css';
const bannerImages = [
    {
        id: 1,
        src: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/cc5/329_548_1c864ec529fb1f49b0f3d35348fc0bcf1/y66wecfe34mdhtzdrk26ljqj0i01zwdz.jpg',
        alt: '2=10%, 3=20%',
        href: '/promos',
    },
    {
        id: 2,
        src: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/317/329_548_1c864ec529fb1f49b0f3d35348fc0bcf1/9iqavq5elw0q369dnw7sxsnugyw0nhqg.jpg',
        alt: 'лучшая',
        href: '/category/zhenskaya-obuv/-128293-spetsialnaya-tsena/',
    },
];
import { Link } from '@tanstack/react-router';

export const BannerSlider = () => {
    const swiperRef = useRef<any>(null);
    const [activeIndex, setActiveIndex] = useState(0);

    return (
        <div className='banner-slider flex flex-col items-center'>
            {/* Слайдер */}
            <div className='w-full'>
                <Swiper
                    modules={[Autoplay]}
                    spaceBetween={0}
                    slidesPerView={1}
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
                    loop={true}
                    className='rounded-lg'
                >
                    {bannerImages.map((image) => (
                        <SwiperSlide key={image.id}>
                            <Link
                                to={image.href}
                                rel='noopener noreferrer'
                                className='flex justify-center items-center'
                            >
                                <img
                                    src={image.src}
                                    alt={image.alt}
                                    className='w-[210px] h-auto rounded-lg'
                                />
                            </Link>
                        </SwiperSlide>
                    ))}
                </Swiper>
            </div>
            <div className='banner-pagination flex justify-center gap-1 mt-7'>
                {bannerImages.map((_, index) => (
                    <button
                        key={index}
                        className={`w-2.5 h-2.5 rounded-full text-xs font-medium transition-all duration-300 border  ${
                            activeIndex === index
                                ? 'bg-blue-600 text-white border-blue-600 scale-110'
                                : 'bg-gray-300 text-gray-700 border-gray-300 hover:bg-gray-100'
                        }`}
                        onClick={() => swiperRef.current?.slideTo(index)}
                    ></button>
                ))}
            </div>
        </div>
    );
};
