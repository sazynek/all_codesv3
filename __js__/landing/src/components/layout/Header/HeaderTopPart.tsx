import { FaVk } from 'react-icons/fa6';
import { FaTelegram } from 'react-icons/fa6';
import { FaInstagram } from 'react-icons/fa6';

import { v4 as uuid } from 'uuid';
const menuItems: string[] = [
    'Доставка',
    'Оплата',
    'Гарантия и возврат',
    'О компании',
    'Салоны',
    'О продукции',
    'Контакты',
];
// #b35424
const socialIcons = [
    { icon: FaVk, size: 32, url: '/' },
    { icon: FaTelegram, size: 32, url: '/' },
    { icon: FaInstagram, size: 32, url: '/' },
];
export const HeaderTopPart = () => {
    return (
        <div className='pt-2 flex flex-col lg:flex-row justify-between gap-4 lg:gap-0'>
            {/* Меню - на мобильных становится вертикальным */}
            <div className='flex justify-center lg:justify-start'>
                <div className='flex flex-wrap justify-center gap-3 md:gap-6 lg:gap-10 text-sm items-center font-semibold'>
                    {menuItems.map((f) => (
                        <a
                            href='/'
                            key={uuid()}
                            className='hover:text-[#b35424] transition-colors duration-200 text-xs sm:text-sm'
                        >
                            {f}
                        </a>
                    ))}
                </div>
            </div>

            {/* Социальные иконки и кнопка входа - на мобильных в одну строку */}
            <div className='flex flex-col sm:flex-row items-center gap-4 sm:gap-6 lg:gap-3'>
                <div className='flex gap-3 items-center order-2 sm:order-1'>
                    {socialIcons.map(({ icon: IconComponent, size, url }) => (
                        <a
                            className='group text-gray-500 hover:text-[#b35424] transition-colors duration-200'
                            href={url}
                            key={uuid()}
                        >
                            <IconComponent
                                size={size}
                                className='group-hover:text-[#b35424] transition-colors duration-200 w-6 h-6 sm:w-8 sm:h-8'
                            />
                        </a>
                    ))}
                </div>

                <a
                    className='flex items-center hover:text-[#b35424] transition-colors duration-200 font-bold text-sm order-1 sm:order-2'
                    href='/'
                >
                    <div className='text-xs sm:text-sm'>Вход / Регистрация</div>
                </a>
            </div>
        </div>
    );
};
