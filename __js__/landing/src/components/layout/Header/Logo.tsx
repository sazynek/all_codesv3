import { FaHeart, FaTrash } from 'react-icons/fa6';
import { DeliverySing } from '../../ui/DeliverySing';
import { Link } from '@tanstack/react-router';
import { Input } from './Input';

export const Logo = () => {
    return (
        <div className='pt-5 flex justify-between items-center gap-5'>
            <Link to='/'>
                <div className='flex gap-5 items-center w-[300px]'>
                    <img src='logo.png' alt='Logo' />
                    <div className='text-center w-fit'>
                        <div className='text-[#422d22] text-center font-bold'>
                            сеть салонов
                        </div>
                        <div className='text-[#422d22] text-3xl font-extrabold text-wrap uppercase text-center'>
                            Немецкая Обувь
                        </div>
                    </div>
                </div>
            </Link>
            {/* <SearchForm width='w-[447px]' />
             */}
            <div className={`w-[447px] relative`}>
                <Input key={'input'} />
            </div>

            <div className='flex flex-col gap-1'>
                <div className='font-bold text-xl text-end'>
                    8 800 550-47-80
                </div>
                <div className='font-bold text-xl text-end'>
                    8 812 509-37-38
                </div>
                <DeliverySing />
            </div>
            <div className='flex gap-3'>
                <FaHeart
                    size={24}
                    color='black'
                    className='items-center flex self-start'
                />
                <div className='items-center self-start text-base font-bold'>
                    Избранное
                </div>
                <span className='text-lg self-start bg-amber-700 rounded-full px-2 py-0 text-white h-fit w-fit'>
                    0
                </span>
            </div>
            <div className='flex gap-2  text-wrap'>
                <FaTrash className='w-fit h-auto' />
                <span className='text-base font-bold'>Ваша корзина пуста</span>
            </div>
        </div>
    );
};
