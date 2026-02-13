import { CategoryMenu } from './CategoryMenu';
import { HeaderTopPart } from './HeaderTopPart';
import { Logo } from './Logo';

export const Header = () => {
    return (
        <div className='container'>
            <HeaderTopPart />
            <Logo />
            <CategoryMenu />
        </div>
    );
};
