/**
 * SpaceQuest - Cascading selector navigation for space domain maps
 */
(function() {
    'use strict';

    // State
    let topics = {};
    let selected = { l1: null, l2: null, l3: null };

    // DOM elements
    const els = {
        level1: null,
        level2: null,
        level3: null,
        buttonsL1: null,
        buttonsL2: null,
        buttonsL3: null,
        resetContainer: null,
        resetBtn: null,
        breadcrumb: null,
        content: null,
        loading: null,
        map: null
    };

    // Initialize
    function init() {
        // Get DOM elements
        els.level1 = document.getElementById('sq-level1');
        els.level2 = document.getElementById('sq-level2');
        els.level3 = document.getElementById('sq-level3');
        els.buttonsL1 = document.getElementById('sq-buttons-l1');
        els.buttonsL2 = document.getElementById('sq-buttons-l2');
        els.buttonsL3 = document.getElementById('sq-buttons-l3');
        els.resetContainer = document.getElementById('sq-reset-container');
        els.resetBtn = document.getElementById('sq-reset');
        els.breadcrumb = document.getElementById('sq-breadcrumb');
        els.content = document.getElementById('sq-content');
        els.loading = document.getElementById('sq-loading');
        els.map = document.getElementById('sq-map');

        // Load topics data
        const dataEl = document.getElementById('sq-topics-data');
        if (dataEl) {
            try {
                let parsed = JSON.parse(dataEl.textContent);
                // Handle double-encoded JSON (Hugo sometimes does this)
                if (typeof parsed === 'string') {
                    parsed = JSON.parse(parsed);
                }
                topics = parsed;
                console.log('Topics loaded:', topics);
                console.log('Topics keys:', Object.keys(topics));
            } catch (e) {
                console.error('Failed to parse topics data:', e);
                return;
            }
        }

        // Bind events
        bindEvents();
    }

    function bindEvents() {
        // L1 buttons (already in DOM)
        els.buttonsL1.addEventListener('click', handleL1Click);

        // L2 and L3 buttons (dynamically added)
        els.buttonsL2.addEventListener('click', handleL2Click);
        els.buttonsL3.addEventListener('click', handleL3Click);

        // Reset button
        els.resetBtn.addEventListener('click', reset);
    }

    function handleL1Click(e) {
        const btn = e.target.closest('.sq-btn');
        if (!btn) return;

        const value = btn.dataset.value;
        selectL1(value);
    }

    function handleL2Click(e) {
        const btn = e.target.closest('.sq-btn');
        if (!btn) return;

        const value = btn.dataset.value;
        selectL2(value);
    }

    function handleL3Click(e) {
        const btn = e.target.closest('.sq-btn');
        if (!btn) return;

        const value = btn.dataset.value;
        selectL3(value);
    }

    function selectL1(value) {
        console.log('selectL1 called with:', value);
        selected.l1 = value;
        selected.l2 = null;
        selected.l3 = null;

        // Update L1 buttons
        updateActiveButton(els.buttonsL1, value);

        // Populate L2
        const l2Data = topics[value];
        console.log('L2 data for', value, ':', l2Data);
        console.log('L2 keys:', l2Data ? Object.keys(l2Data) : 'none');
        if (l2Data) {
            populateButtons(els.buttonsL2, Object.keys(l2Data));
            console.log('els.level2:', els.level2);
            show(els.level2);
        }

        // Hide L3 and content
        hide(els.level3);
        hide(els.content);

        // Show reset
        show(els.resetContainer);

        // Update breadcrumb
        updateBreadcrumb();
    }

    function selectL2(value) {
        selected.l2 = value;
        selected.l3 = null;

        // Update L2 buttons
        updateActiveButton(els.buttonsL2, value);

        // Populate L3
        const l3Data = topics[selected.l1][value];
        if (l3Data && Array.isArray(l3Data)) {
            populateButtons(els.buttonsL3, l3Data);
            show(els.level3);
        }

        // Hide content
        hide(els.content);

        // Update breadcrumb
        updateBreadcrumb();
    }

    function selectL3(value) {
        selected.l3 = value;

        // Update L3 buttons
        updateActiveButton(els.buttonsL3, value);

        // Update breadcrumb
        updateBreadcrumb();

        // Load map content
        loadMapContent();
    }

    function populateButtons(container, items) {
        container.innerHTML = items.map(item =>
            `<button class="sq-btn" data-level="${container.id.slice(-1)}" data-value="${item}">${formatLabel(item)}</button>`
        ).join('');
    }

    function updateActiveButton(container, value) {
        container.querySelectorAll('.sq-btn').forEach(btn => {
            btn.classList.toggle('sq-active', btn.dataset.value === value);
        });
    }

    function formatLabel(str) {
        // Convert kebab-case or space-separated to Title Case
        return str.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }

    function toSlug(str) {
        // Convert "orbital transfer vehicle" to "orbital-transfer-vehicle"
        return str.toLowerCase().replace(/\s+/g, '-');
    }

    function updateBreadcrumb() {
        const parts = [];
        if (selected.l1) parts.push(`<span>${formatLabel(selected.l1)}</span>`);
        if (selected.l2) parts.push(`<span>${formatLabel(selected.l2)}</span>`);
        if (selected.l3) parts.push(`<span>${formatLabel(selected.l3)}</span>`);

        if (parts.length > 0) {
            els.breadcrumb.innerHTML = parts.join(' → ');
            show(els.breadcrumb);
        } else {
            hide(els.breadcrumb);
        }
    }

    function loadMapContent() {
        if (!selected.l1 || !selected.l2 || !selected.l3) return;

        // Detect language prefix from current URL
        const langMatch = window.location.pathname.match(/^\/(it)\//);
        const langPrefix = langMatch ? `/${langMatch[1]}` : '';

        // Build URL: /[lang]/maps/{l1}/{l2}/{l3-slug}/?embed=1
        const url = `${langPrefix}/maps/${selected.l1}/${selected.l2}/${toSlug(selected.l3)}/?embed=1`;

        // Show loading
        show(els.content);
        show(els.loading);
        els.map.innerHTML = '';

        // Create iframe to load map (jsvis requires scripts to execute)
        const iframe = document.createElement('iframe');
        iframe.src = url;
        iframe.className = 'sq-iframe';
        iframe.setAttribute('frameborder', '0');
        iframe.setAttribute('loading', 'lazy');

        iframe.onload = function() {
            hide(els.loading);
        };

        iframe.onerror = function() {
            const errorMsg = langPrefix === '/it'
                ? `<p>Impossibile caricare la mappa. <a href="${url}" target="_blank">Apri in una nuova scheda</a></p>`
                : `<p>Could not load map. <a href="${url}" target="_blank">Open in new tab</a></p>`;
            els.map.innerHTML = errorMsg;
            hide(els.loading);
        };

        els.map.appendChild(iframe);
    }

    function reset() {
        selected = { l1: null, l2: null, l3: null };

        // Clear active states
        els.buttonsL1.querySelectorAll('.sq-btn').forEach(btn => btn.classList.remove('sq-active'));
        els.buttonsL2.innerHTML = '';
        els.buttonsL3.innerHTML = '';

        // Hide elements
        hide(els.level2);
        hide(els.level3);
        hide(els.resetContainer);
        hide(els.breadcrumb);
        hide(els.content);

        // Clear map
        els.map.innerHTML = '';
    }

    function show(el) {
        if (el) el.classList.remove('sq-hidden');
    }

    function hide(el) {
        if (el) el.classList.add('sq-hidden');
    }

    // Start when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
