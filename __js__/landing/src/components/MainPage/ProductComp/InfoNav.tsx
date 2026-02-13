import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import type { InfoNavProps, NavItem } from '../../../types';

export const InfoNav = ({
    onNext,
    onPrev,
    activeCategory,
    onCategoryChange,
}: InfoNavProps) => {
    const navItems: NavItem[] = [
        {
            id: '1',
            title: 'Популярные товары',
            isActive: true,
        },
        {
            id: '2',
            title: 'Новинки',
            isActive: false,
        },
        {
            id: '3',
            title: 'Распродажа',
            isActive: false,
        },
    ];

    return (
        <div className='info__nav nav-info container'>
            <div className='nav-info__list flex justify-between items-center'>
                {/* Категории справа */}
                <div className='flex space-x-10'>
                    {navItems.map((item) => {
                        const isActive = item.id === activeCategory;
                        return (
                            <div
                                key={item.id}
                                className={`nav-info__item group  ${
                                    isActive
                                        ? 'active text-orange-600 font-bold'
                                        : 'text-gray-500 hover:text-orange-500'
                                }`}
                            >
                                <button
                                    onClick={() => onCategoryChange(item.id)}
                                    className='cursor-pointer nav-info__link font-medium transition-colors duration-200 py-3 relative'
                                >
                                    {item.title}
                                    {isActive && (
                                        <div className='absolute bottom-0 left-0 w-full h-0.5 bg-orange-500'></div>
                                    )}
                                    {!isActive && (
                                        <div className='absolute bottom-0 left-0 w-0 h-0.5 bg-orange-400 transition-all duration-300 group-hover:w-full'></div>
                                    )}
                                </button>
                            </div>
                        );
                    })}
                </div>
                {/* Стрелочки слева */}
                <div className='flex space-x-3'>
                    <button
                        onClick={onPrev}
                        className='w-10 h-10 flex items-center justify-center border-2 border-orange-500 text-orange-500 rounded-full hover:bg-orange-500 hover:text-white transition-all duration-200 shadow-sm'
                    >
                        <FiChevronLeft className='w-5 h-5' />
                    </button>
                    <button
                        onClick={onNext}
                        className='w-10 h-10 flex items-center justify-center border-2 border-orange-500 text-orange-500 rounded-full hover:bg-orange-500 hover:text-white transition-all duration-200 shadow-sm'
                    >
                        <FiChevronRight className='w-5 h-5' />
                    </button>
                </div>
            </div>
        </div>
    );
};
