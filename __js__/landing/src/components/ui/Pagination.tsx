// components/ui/Pagination.tsx
import ReactPaginate from 'react-paginate';
import './pagination.css';
interface PaginationProps {
    currentPage: number;
    totalPages: number;
    onPageChange: (selectedPage: number) => void;
}

export function Pagination({
    currentPage,
    totalPages,
    onPageChange,
}: PaginationProps) {
    const handlePageClick = (event: { selected: number }) => {
        // react-paginate использует 0-based индексы, нам нужны 1-based
        onPageChange(event.selected + 1);
    };

    if (totalPages <= 1) return null;

    return (
        <div className='pagination__row mt-8'>
            <span className='pagination__title'>Страницы:</span>

            {/* Десктопная версия */}
            <div className='hidden md:block'>
                <ReactPaginate
                    breakLabel='...'
                    nextLabel='>'
                    onPageChange={handlePageClick}
                    pageRangeDisplayed={3}
                    marginPagesDisplayed={2}
                    pageCount={totalPages}
                    previousLabel='<'
                    forcePage={currentPage - 1} // Конвертируем в 0-based индекс
                    // Классы для стилизации
                    containerClassName='pagination__list flex gap-2'
                    pageClassName='pagination__item'
                    pageLinkClassName='pagination__link px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 transition-colors'
                    activeClassName='active'
                    activeLinkClassName='bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
                    breakClassName='pagination__item'
                    breakLinkClassName='pagination__three-dots px-3 py-2'
                    previousClassName='pagination__item'
                    previousLinkClassName='pagination__link px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 transition-colors'
                    nextClassName='pagination__item'
                    nextLinkClassName='pagination__link px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 transition-colors'
                    disabledClassName='opacity-50 cursor-not-allowed'
                    disabledLinkClassName='hover:bg-transparent'
                />
            </div>

            {/* Мобильная версия */}
            <div className='md:hidden'>
                <ReactPaginate
                    breakLabel='...'
                    nextLabel='>'
                    onPageChange={handlePageClick}
                    pageRangeDisplayed={2}
                    marginPagesDisplayed={1}
                    pageCount={totalPages}
                    previousLabel='<'
                    forcePage={currentPage - 1}
                    // Классы для мобильной версии
                    containerClassName='pagination__list pagination__list--mobile flex gap-1'
                    pageClassName='pagination__item'
                    pageLinkClassName='pagination__link px-2 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50'
                    activeClassName='active'
                    activeLinkClassName='bg-blue-600 text-white border-blue-600'
                    breakClassName='pagination__item'
                    breakLinkClassName='pagination__three-dots px-2 py-1'
                    previousClassName='pagination__item'
                    previousLinkClassName='pagination__link px-2 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50'
                    nextClassName='pagination__item'
                    nextLinkClassName='pagination__link px-2 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50'
                    disabledClassName='opacity-50 cursor-not-allowed'
                />
            </div>
        </div>
    );
}
