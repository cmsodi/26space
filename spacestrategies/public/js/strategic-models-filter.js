/**
 * Strategic Models Two-Level Filter System
 * Level 1: Category dropdown
 * Level 2: Methods buttons
 */
(function () {
  'use strict';

  // Check if we're on the strategic-models page
  const strategicModelsDataEl = document.getElementById('strategic-models-data');
  const articlesDataEl = document.getElementById('articles-data');

  if (!strategicModelsDataEl || !articlesDataEl) {
    return; // Not on strategic-models page
  }

  // Parse data from embedded JSON
  let strategicModels = JSON.parse(strategicModelsDataEl.textContent);
  let articlesData = JSON.parse(articlesDataEl.textContent);

  // Hugo jsonify sometimes double-encodes, so check if we need to parse again
  if (typeof strategicModels === 'string') {
    strategicModels = JSON.parse(strategicModels);
  }
  if (typeof articlesData === 'string') {
    articlesData = JSON.parse(articlesData);
  }

  // DOM elements
  const categorySelect = document.getElementById('category-select');
  const categoryInfo = document.getElementById('category-info');
  const categoryName = document.getElementById('category-name');
  const categoryDescription = document.getElementById('category-description');

  const methodsContainer = document.getElementById('methods-container');
  const methodInfo = document.getElementById('method-info');
  const methodName = document.getElementById('method-name');
  const methodDescription = document.getElementById('method-description');
  const methodAudience = document.getElementById('method-audience');
  const methodUtility = document.getElementById('method-utility');

  const articlesContainer = document.getElementById('articles-container');
  const articlesList = document.getElementById('articles-list');

  // Detect page language (check URL path for /it/ or html lang attribute)
  const isItalian = window.location.pathname.startsWith('/it/') ||
                    document.documentElement.lang === 'it' ||
                    document.documentElement.lang === 'it-IT';

  // State
  let selectedCategory = null;
  let selectedMethod = null;

  // Event: Category selection (Level 1)
  categorySelect.addEventListener('change', function(e) {
    const categoryId = e.target.value;

    if (!categoryId) {
      // Reset all
      resetView();
      return;
    }

    // Find selected category
    selectedCategory = strategicModels.find(cat => cat.id === categoryId);

    if (selectedCategory) {
      showCategoryInfo(selectedCategory);
      renderMethods(selectedCategory.methods);

      // Reset method selection
      selectedMethod = null;
      hideMethodInfo();
      hideArticles();
    }
  });

  // Show category info
  function showCategoryInfo(category) {
    categoryName.textContent = category.name;
    categoryDescription.textContent = isItalian && category.description_it
      ? category.description_it
      : category.description;
    categoryInfo.style.display = 'block';
  }

  // Render methods buttons (Level 2)
  function renderMethods(methods) {
    methodsContainer.innerHTML = '';

    methods.forEach(method => {
      const button = document.createElement('button');
      button.className = 'sm-method-btn';
      button.dataset.methodId = method.id;
      button.innerHTML = `<span>${method.name}</span>`;

      button.addEventListener('click', function() {
        selectMethod(method);

        // Visual feedback: active state
        document.querySelectorAll('.sm-method-btn').forEach(btn => {
          btn.classList.remove('active');
        });
        button.classList.add('active');
      });

      methodsContainer.appendChild(button);
    });

    methodsContainer.style.display = 'grid';
  }

  // Select method and show details
  function selectMethod(method) {
    selectedMethod = method;

    // Show method info with language support
    methodName.textContent = method.name;
    methodDescription.textContent = isItalian && method.description_it
      ? method.description_it
      : method.description;
    methodAudience.textContent = isItalian && method.target_audience_it
      ? method.target_audience_it
      : method.target_audience;
    methodUtility.textContent = isItalian && method.strategic_utility_it
      ? method.strategic_utility_it
      : method.strategic_utility;
    methodInfo.style.display = 'block';

    // Filter and show articles
    filterArticles(method.id);
  }

  // Filter articles by method ID
  function filterArticles(methodId) {
    const filteredArticles = articlesData.filter(article =>
      article.id === methodId
    );

    if (filteredArticles.length === 0) {
      articlesList.innerHTML = '<p class="sm-no-articles">No articles found for this method.</p>';
    } else {
      articlesList.innerHTML = filteredArticles.map(article => `
        <article class="sm-article-item">
          <div class="sm-article-date">${formatDate(article.date)}</div>
          <h4 class="sm-article-title">
            <a href="${article.url}">${article.title}</a>
          </h4>
          ${article.description ? `<p class="sm-article-desc">${article.description}</p>` : ''}
        </article>
      `).join('');
    }

    articlesContainer.style.display = 'block';
  }

  // Helper: format date
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  // Hide method info
  function hideMethodInfo() {
    methodInfo.style.display = 'none';
  }

  // Hide articles
  function hideArticles() {
    articlesContainer.style.display = 'none';
  }

  // Reset entire view
  function resetView() {
    categoryInfo.style.display = 'none';
    methodsContainer.style.display = 'none';
    hideMethodInfo();
    hideArticles();
    selectedCategory = null;
    selectedMethod = null;
  }

})();
