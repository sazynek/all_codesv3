import { createFileRoute } from '@tanstack/react-router';

import { Link } from '@tanstack/react-router';
import { Breadcrumbs } from '../../components/ui/Breadcrumbs';
import { BannerSlider } from '../../components/ui/Banner';

export const Route = createFileRoute('/discount/')({
    component: Discount,
});

function Discount() {
    const breadcrumbItems = [
        { label: 'Главная', href: '/' },
        { label: 'Бонусная программа', href: '/discount' },
    ];

    const menuItems = [
        { label: 'Доставка', href: '/delivery' },
        { label: 'Оплата', href: '/payment' },
        { label: 'Гарантия и возврат', href: '/guarantee' },
        { label: 'О компании', href: '/about-company' },
        { label: 'Салоны', href: '/salons' },
        { label: 'О продукции', href: '/about-products' },
        { label: 'Контакты', href: '/contacts' },
    ];

    return (
        <div className='container mx-auto px-4 py-8'>
            <div className='content__inner-wrapper'>
                {/* Хлебные крошки */}
                <Breadcrumbs items={breadcrumbItems} />

                <div className='content__row flex flex-col lg:flex-row gap-8'>
                    {/* Левая колонка - основной контент */}
                    <div className='content__col-left flex-1 text-left'>
                        <main className='main'>
                            <div className='text space-y-6'>
                                <h3 className='text-xl font-semibold'>
                                    Бонусная программа временно недоступна в
                                    интернет-магазине.
                                </h3>

                                <h2 className='text-2xl font-bold'>
                                    Бонусная программа лояльности для салонов
                                    «НЕМЕЦКАЯ ОБУВЬ».
                                </h2>

                                <p>
                                    Для каждого участника создается бонусный
                                    счет. Обязательные реквизиты бонусного
                                    счета: фамилия, имя, отчество, номер
                                    мобильного телефона, дата рождения.
                                    Покупатель собственноручно заполняет анкету
                                    и дает согласие на обработку данных.
                                </p>

                                <p>
                                    К этому счету привязывается виртуальная
                                    карта бонусной программы. На одно физическое
                                    лицо может быть оформлена только одна
                                    виртуальная бонусная карта.
                                </p>

                                <p>
                                    <strong>1 бонус = 1 рубль.</strong>
                                </p>

                                <h2 className='text-2xl font-bold mt-8'>
                                    Правила начисления бонусов
                                </h2>

                                <div className='overflow-x-auto'>
                                    <table className='w-full border-collapse border border-gray-300 text-sm'>
                                        <tbody>
                                            <tr className='bg-gray-50'>
                                                <td className='border border-gray-300 p-3 font-semibold'>
                                                    Общая сумма покупок
                                                </td>
                                                <td className='border border-gray-300 p-3 font-semibold'>
                                                    Начисление бонусов
                                                </td>
                                            </tr>
                                            <tr>
                                                <td className='border border-gray-300 p-3'>
                                                    до 50'000 руб.
                                                </td>
                                                <td className='border border-gray-300 p-3'>
                                                    3% от суммы покупок
                                                </td>
                                            </tr>
                                            <tr className='bg-gray-50'>
                                                <td className='border border-gray-300 p-3'>
                                                    от 50'001 до 120'000 руб.
                                                </td>
                                                <td className='border border-gray-300 p-3'>
                                                    5% от суммы покупок
                                                </td>
                                            </tr>
                                            <tr>
                                                <td className='border border-gray-300 p-3'>
                                                    от 120'001 руб.
                                                </td>
                                                <td className='border border-gray-300 p-3'>
                                                    7% от суммы покупок
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>

                                <ul className='list-disc list-inside space-y-2 ml-4'>
                                    <li>
                                        Бонусные баллы начисляются в момент
                                        совершения покупки и активируются на 15
                                        календарный день с момента начисления.
                                    </li>
                                    <li>
                                        <strong>1 000 бонусов</strong>{' '}
                                        начисляются единовременно при обмене
                                        пластиковой Дисконтной карты «Немецкая
                                        обувь».
                                    </li>
                                    <li>
                                        <strong>500 бонусов</strong> начисляются
                                        и активируются за 7 дней до дня рождения
                                        покупателя и действуют в течение 20
                                        дней.
                                    </li>
                                </ul>

                                <h2 className='text-2xl font-bold mt-8'>
                                    Правила использования бонусов:
                                </h2>

                                <p>
                                    Бонусами можно воспользоваться в течение{' '}
                                    <strong>10 месяцев</strong> с момента их
                                    начисления.
                                </p>

                                <p>
                                    Бонусы можно использовать в качестве скидки
                                    при оплате обуви, кожгалантереи и
                                    сопутствующих средств, скидка не может
                                    превышать <strong>30%</strong> от
                                    первоначальной стоимости товара. При этом
                                    скидки не суммируются с другими скидками и
                                    акциями.
                                </p>

                                <p>
                                    Списание бонусов происходит при
                                    подтверждении кода из СМС, отправленный на
                                    номер телефона, привязанного к бонусному
                                    счету.
                                </p>

                                <p>
                                    Бонусами нельзя воспользоваться при покупке
                                    товара со скидками и специальными ценами.
                                </p>

                                <p>
                                    Бонусы не начисляются и не используются при
                                    покупке подарочных сертификатов и оплате
                                    подарочными сертификатами.
                                </p>

                                <p>
                                    В случае возврата товара, покупателю
                                    возвращаются использованные бонусы за
                                    покупку данного товара с первоначальным
                                    сроком действия, при этом начисленные бонусы
                                    за возвращённый товар автоматически
                                    списываются с бонусного счёта покупателя.
                                </p>

                                <p>
                                    Информацию о начислении и списании бонусов
                                    можно уточнить на кассе магазина.
                                </p>
                            </div>
                        </main>
                    </div>

                    {/* Правая колонка - сайдбар */}
                    <div className='content__col-right w-full lg:w-96 shrink-0 text-left'>
                        <aside className='aside space-y-6'>
                            {/* Меню */}
                            <div className='menu bg-white rounded-lg shadow-sm border border-gray-200'>
                                <ul className='menu__list divide-y divide-gray-200'>
                                    {menuItems.map((item, index) => (
                                        <li key={index} className='menu__item'>
                                            <Link
                                                to={item.href}
                                                className='menu__link flex justify-between items-center px-4 py-4 text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer group'
                                            >
                                                <span className='font-bold text-lg'>
                                                    {item.label}
                                                </span>
                                                <span className='text-gray-400 group-hover:text-blue-600 transition-colors'>
                                                    ›
                                                </span>
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* Баннер */}
                            <div className='banner'>
                                <BannerSlider />
                            </div>
                        </aside>
                    </div>
                </div>
            </div>
        </div>
    );
}
