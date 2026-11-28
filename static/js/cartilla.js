(() => {
  const books = Array.from(document.querySelectorAll('[data-cartilla]'));

  books.forEach((book, bookIndex) => {
    let pages = Array.from(book.querySelectorAll('[data-cartilla-page]'));
    const rootIsPage = pages.length === 0;
    if (pages.length === 0) {
      book.setAttribute('data-cartilla-page', '');
      pages = [book];
    }

    book.setAttribute('role', 'region');
    book.setAttribute('aria-roledescription', 'cartilla');
    if (pages.length > 1) book.tabIndex = 0;
    if (!book.hasAttribute('aria-label')) {
      book.setAttribute('aria-label', 'Cartilla VeredalApp');
    }

    pages.forEach((page, pageIndex) => {
      if (!page.id) page.id = `cartilla-${bookIndex + 1}-page-${pageIndex + 1}`;
      page.hidden = pageIndex !== 0;
      page.setAttribute('aria-hidden', pageIndex === 0 ? 'false' : 'true');
      if (!rootIsPage) {
        page.setAttribute('role', 'group');
        page.setAttribute('aria-roledescription', 'página');
      }
      if (page.dataset.cartillaLabel) {
        page.setAttribute('aria-label', page.dataset.cartillaLabel);
      }
    });

    const controls = document.createElement('nav');
    controls.className = 'cartilla-controls';
    controls.setAttribute('aria-label', 'Navegación de páginas');

    const previousButton = document.createElement('button');
    previousButton.type = 'button';
    previousButton.className = 'cartilla-tab cartilla-tab-previous';
    previousButton.setAttribute('aria-label', 'Página anterior');
    previousButton.setAttribute('aria-controls', pages[0].id);
    previousButton.textContent = '‹';

    const counter = document.createElement('span');
    counter.className = 'cartilla-counter';
    counter.setAttribute('aria-live', 'polite');
    counter.setAttribute('aria-label', `Página 1 de ${pages.length}`);
    counter.textContent = `Página 1 de ${pages.length}`;

    const nextButton = document.createElement('button');
    nextButton.type = 'button';
    nextButton.className = 'cartilla-tab cartilla-tab-next';
    nextButton.setAttribute('aria-label', 'Página siguiente');
    nextButton.setAttribute('aria-controls', pages[0].id);
    nextButton.textContent = '›';

    controls.append(previousButton, counter, nextButton);
    book.appendChild(controls);

    let currentPage = 0;
    const showPage = (index) => {
      if (index < 0 || index >= pages.length || index === currentPage) return;

      pages[currentPage].hidden = true;
      pages[currentPage].setAttribute('aria-hidden', 'true');
      currentPage = index;
      pages[currentPage].hidden = false;
      pages[currentPage].setAttribute('aria-hidden', 'false');
      previousButton.disabled = currentPage === 0;
      nextButton.disabled = currentPage === pages.length - 1;
      previousButton.setAttribute('aria-controls', pages[currentPage].id);
      nextButton.setAttribute('aria-controls', pages[currentPage].id);
      counter.textContent = `Página ${currentPage + 1} de ${pages.length}`;
      counter.setAttribute(
        'aria-label',
        `Página ${currentPage + 1} de ${pages.length}${pages[currentPage].dataset.cartillaLabel ? `: ${pages[currentPage].dataset.cartillaLabel}` : ''}`
      );
      window.dispatchEvent(new Event('resize'));
    };

    previousButton.disabled = true;
    nextButton.disabled = pages.length < 2;
    previousButton.addEventListener('click', () => showPage(currentPage - 1));
    nextButton.addEventListener('click', () => showPage(currentPage + 1));

    book.addEventListener('keydown', (event) => {
      if (event.target.closest('input, textarea, select, button, a, [contenteditable="true"]')) return;
      if (event.key === 'ArrowRight') {
        event.preventDefault();
        showPage(currentPage + 1);
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault();
        showPage(currentPage - 1);
      }
    });
  });
})();
