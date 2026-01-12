/**
 * Tag Filter with AND/OR logic
 * - OR within same group (column)
 * - AND between different groups
 */
(function () {
  'use strict';

  function initTagFilter() {
    // Check if List.js is loaded
    if (typeof List === 'undefined') {
      console.error('TagFilter: List.js not loaded');
      return;
    }

    // Check if we're on the tags page
    const listContainer = document.getElementById('js-list');
    if (!listContainer) {
      return;
    }

    // List.js configuration
    const options = {
      valueNames: ['title', 'date', 'frameworks', 'technologies', 'stakeholders', 'purposes'],
      listClass: 'js-items'
    };

    const items = new List('js-list', options);

    // Active filters state
    const activeFilters = {
      frameworks: [],
      technologies: [],
      stakeholders: [],
      purposes: []
    };

    // DOM references (using sp-* classes)
    const filterCells = document.querySelectorAll('.sp-filter-cell');
    const resetBtn = document.querySelector('.sp-filter-reset');
    const resultsCount = document.querySelector('.sp-results-count');

    // Update results counter
    function updateCount() {
      const visible = items.matchingItems.length;
      const total = items.items.length;
      if (resultsCount) {
        if (hasActiveFilters()) {
          resultsCount.textContent = visible + ' of ' + total + ' articles';
        } else {
          resultsCount.textContent = total + ' articles';
        }
      }
    }

    // Check if any filter is active
    function hasActiveFilters() {
      return Object.values(activeFilters).some(arr => arr.length > 0);
    }

    // Toggle cell selection
    filterCells.forEach(function(cell) {
      cell.addEventListener('click', function() {
        const group = this.closest('.filter-group').dataset.group;
        const value = this.dataset.value;

        // Toggle active class (CSS handles the styling)
        this.classList.toggle('active');

        // Update filters array
        const index = activeFilters[group].indexOf(value);
        if (index === -1) {
          activeFilters[group].push(value);
        } else {
          activeFilters[group].splice(index, 1);
        }

        applyFilters();
      });
    });

    // Reset all filters
    if (resetBtn) {
      resetBtn.addEventListener('click', function() {
        // Remove active class from all cells
        filterCells.forEach(function(cell) {
          cell.classList.remove('active');
        });

        // Clear all arrays
        activeFilters.frameworks = [];
        activeFilters.technologies = [];
        activeFilters.stakeholders = [];
        activeFilters.purposes = [];

        // Show all
        items.filter();
        items.sort('date', { order: 'desc' });
        updateCount();
      });
    }

    // Apply AND/OR filter logic
    function applyFilters() {
      items.filter(function(item) {
        const v = item.values();

        // For each group: if filters active, at least one must match (OR)
        // Between groups: all must be satisfied (AND)
        const matchFrameworks = matchGroup(activeFilters.frameworks, v.frameworks);
        const matchTechnologies = matchGroup(activeFilters.technologies, v.technologies);
        const matchStakeholders = matchGroup(activeFilters.stakeholders, v.stakeholders);
        const matchPurposes = matchGroup(activeFilters.purposes, v.purposes);

        // AND between the 4 groups
        return matchFrameworks && matchTechnologies && matchStakeholders && matchPurposes;
      });

      // Keep sorted by date (newest first)
      items.sort('date', { order: 'desc' });
      updateCount();
    }

    // Helper: OR within group
    function matchGroup(filters, itemValue) {
      // If no filter active in group, pass (true)
      if (filters.length === 0) return true;

      // Otherwise: at least one filter must be present in item
      const itemValueLower = (itemValue || '').toLowerCase();
      return filters.some(function(f) {
        return itemValueLower.indexOf(f.toLowerCase()) !== -1;
      });
    }

    // Initial count
    updateCount();
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTagFilter);
  } else {
    initTagFilter();
  }
})();
