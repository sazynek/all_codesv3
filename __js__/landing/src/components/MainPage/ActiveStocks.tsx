interface Stocks {
    src: string;
    url: string;
    alt: string;
}
export const ActiveStocks = () => {
    let stocks: Stocks[] = [
        {
            src: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/571/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/nbmdlfgre2vt6ezvc1tyvxfh0wxhm3i1.jpg',
            url: 'https://www.немецкаяобувь.com/promos/dni-brenda-tamaris2/',
            alt: 'BestStock 1',
        },
        {
            src: 'https://www.немецкаяобувь.com/upload/resize_cache/iblock/647/690_340_2c864ec529fb1f49b0f3d35348fc0bcf1/ys18ff1tme5wjiz1zrlxebe4ux0aa4tj.jpg',
            url: 'https://www.немецкаяобувь.com/promos/luchshaya-tsena-na-izbrannye-modeli24/',
            alt: 'BestStock 2',
        },
    ];
    return (
        <div className='container'>
            <h2 className='text-start text-3xl font-bold mb-10 mt-15'>
                Действующие акции
            </h2>
            <div className='flex justify-between gap-2'>
                {stocks.map((c, index) => (
                    <div
                        key={index}
                        className='relative group overflow-hidden rounded-lg'
                    >
                        <a href={c.url} className='block'>
                            <img
                                src={c.src}
                                alt={c.alt}
                                className='w-full h-auto transition-transform duration-300 group-hover:scale-105'
                            />
                            {/* Эффект затемнения при наведении */}
                            <div className='absolute inset-0 bg-black opacity-0 group-hover:opacity-30 transition-opacity duration-300'></div>
                        </a>
                    </div>
                ))}
            </div>
        </div>
    );
};
