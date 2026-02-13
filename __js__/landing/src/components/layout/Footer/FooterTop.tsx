import { FaVk } from 'react-icons/fa6';

import { FaTelegram } from 'react-icons/fa6';

import type { ReactElement } from 'react';
import { FooterConfidential } from './FooterConfidential';
import { Brand } from './Brands';
import { DeliverySing } from '../../ui/DeliverySing';

interface FooterLink {
    id: string;
    title: string;
    url: string;
}

interface FooterColumn {
    id: string;
    title: string;
    links: FooterLink[];
}

interface SocialLink {
    id: string;
    name: string;
    url: string;
    icon: ReactElement;
}

export const FooterTop = () => {
    // Данные для колонок
    const footerColumns: FooterColumn[] = [
        {
            id: '1',
            title: 'Каталог товаров',
            links: [
                {
                    id: '1-1',
                    title: 'Женская обувь',
                    url: '/catalog/zhenskaya-obuv/',
                },
                {
                    id: '1-2',
                    title: 'Мужская обувь',
                    url: '/catalog/muzhskaya-obuv/',
                },
                { id: '1-3', title: 'Сумки', url: '/catalog/sumki/' },
                {
                    id: '1-4',
                    title: 'Сопутствующие товары',
                    url: '/catalog/soputstvuyushchie-tovary/',
                },
                { id: '1-5', title: 'Бренды', url: '/catalog/brendy/' },
            ],
        },
        {
            id: '2',
            title: 'Для покупателей',
            links: [
                { id: '2-1', title: 'Доставка', url: '/delivery/' },
                { id: '2-2', title: 'Оплата', url: '/payment/' },
                { id: '2-3', title: 'Гарантия и возврат', url: '/guarantee/' },
                { id: '2-4', title: 'Акции', url: '/promos/' },
                {
                    id: '2-5',
                    title: 'Дисконтная программа',
                    url: '/discounts/',
                },
                {
                    id: '2-6',
                    title: 'Как сделать заказ',
                    url: '/how-to-make-order/',
                },
                { id: '2-7', title: 'Публичная оферта', url: '/public-offer/' },
            ],
        },
        {
            id: '3',
            title: 'О компании',
            links: [
                { id: '3-1', title: 'О компании', url: '/about-company/' },
                {
                    id: '3-2',
                    title: 'Вакансии',
                    url: '/about-company/vakansii/',
                },
                { id: '3-3', title: 'Салоны', url: '/salons/' },
                { id: '3-4', title: 'О продукции', url: '/about-products/' },
                { id: '3-5', title: 'Контакты', url: '/contacts/' },
            ],
        },
    ];

    const socialLinks: SocialLink[] = [
        {
            id: 's-1',
            name: 'Vkontakte',
            url: 'https://vk.com/deutscheschuhe',
            icon: <FaVk className='w-5 h-5' />,
        },
        {
            id: 's-2',
            name: 'Одноклассники',
            url: 'https://ok.ru/group/55380336967825',
            icon: <FaVk className='w-5 h-5' />,
        },
        {
            id: 's-3',
            name: 'Телеграм',
            url: 'https://t.me/deutscheschuhe',
            icon: <FaTelegram className='w-5 h-5' />,
        },
    ];

    // Телефоны
    const phones = [
        { id: 'p-1', number: '8 800 550-47-80', href: 'tel:88005504780' },
        { id: 'p-2', number: '8 812 509-37-38', href: 'tel:+78125093738' },
    ];

    return (
        <footer className=' text-black mt-10'>
            <Brand />
            {/* Верхняя часть футера */}
            <div className='container'>
                <div className=' mx-auto px-4 py-8 mt-5'>
                    <div className='flex flex-col lg:flex-row gap-8 lg:gap-12'>
                        {/* Три колонки с навигацией */}
                        <div className='flex-1 grid grid-cols-1 md:grid-cols-3 gap-8'>
                            {footerColumns.map((column) => (
                                <div
                                    key={column.id}
                                    className='space-y-4 text-start'
                                >
                                    <h3 className='text-lg font-semibold text-black mb-4 line'>
                                        {column.title}
                                    </h3>
                                    <ul className='space-y-2'>
                                        {column.links.map((link) => (
                                            <li key={link.id}>
                                                <a
                                                    href={link.url}
                                                    className='text-black hover:text-[#b35424] transition-colors duration-200 text-sm'
                                                >
                                                    {link.title}
                                                </a>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>

                        {/* Контактная информация - отдельная колонка справа */}
                        <div className='lg:w-80 space-y-6 text-end flex flex-col justify-between '>
                            {/* Телефоны */}
                            <div className=''>
                                {phones.map((phone, index) => (
                                    <div
                                        key={phone.id}
                                        className={
                                            index === phones.length - 1
                                                ? 'mb-3'
                                                : ''
                                        }
                                    >
                                        <a
                                            href={phone.href}
                                            className='text-xl text-black font-bold'
                                        >
                                            {phone.number}
                                        </a>
                                    </div>
                                ))}
                                {/* Кнопка заказа звонка */}
                                <DeliverySing />
                            </div>
                            {/* Социальные сети */}
                            <div className='space-y-3 text-end'>
                                <h4 className='text-sm font-semibold text-gray-400'>
                                    Мы в соцсетях
                                </h4>
                                <div className='flex space-x-2 justify-end'>
                                    {socialLinks.map((social) => (
                                        <a
                                            key={social.id}
                                            href={social.url}
                                            target='_blank'
                                            rel='noopener noreferrer'
                                            className='w-9 h-9 bg-[#b35424] text-white rounded-full flex items-center justify-center hover:bg-[#9e4a20] transition-colors duration-200'
                                            aria-label={social.name}
                                        >
                                            <span className='text-sm font-medium'>
                                                {social.icon}
                                            </span>
                                        </a>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <FooterConfidential />
        </footer>
    );
};
