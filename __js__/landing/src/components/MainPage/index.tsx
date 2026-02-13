import { ActiveStocks } from './ActiveStocks';
import { Categories } from './Categies';

import { ProductComp } from './ProductComp';
import { HeroSlider } from './SwiperComp';

export const MainPage = () => {
    return (
        <>
            <HeroSlider />
            <Categories />
            <ActiveStocks />
            <ProductComp /> {/* <InfoNav />   */}
        </>
    );
};
