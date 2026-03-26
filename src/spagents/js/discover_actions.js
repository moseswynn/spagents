() => {
    const actions = [];
    const seen = new Set();
    const processedEls = new WeakSet();
    const actionElements = [];  // parallel array: the DOM element for each action

    function addAction(el, actionType, description, selector) {
        if (seen.has(selector)) return;
        seen.add(selector);
        // Use describeElement for the label — it checks aria-label, text,
        // title, placeholder, etc. in priority order
        const label = describeElement(el);
        actions.push({
            selector,
            action_type: actionType,
            description,
            element_text: label || null,
        });
        actionElements.push(el);
    }

    function getSelector(el) {
        // Try ID first
        if (el.id) return '#' + CSS.escape(el.id);

        // Try unique aria-label
        const label = el.getAttribute('aria-label');
        if (label) {
            const tag = el.tagName.toLowerCase();
            const sel = `${tag}[aria-label="${CSS.escape(label)}"]`;
            if (document.querySelectorAll(sel).length === 1) return sel;
        }

        // Try unique role + text combo
        const role = el.getAttribute('role');
        if (role) {
            const text = (el.textContent || '').trim();
            if (text && text.length < 50) {
                // This is a heuristic — check if role+text is unique enough
                const sel = `[role="${role}"]`;
                const candidates = document.querySelectorAll(sel);
                const matching = Array.from(candidates).filter(c =>
                    c.textContent.trim() === text
                );
                if (matching.length === 1) {
                    // Can't express this as a pure CSS selector, fall through
                }
            }
        }

        // Try data-testid
        const testId = el.getAttribute('data-testid');
        if (testId) {
            const sel = `[data-testid="${CSS.escape(testId)}"]`;
            if (document.querySelectorAll(sel).length === 1) return sel;
        }

        // Build nth-of-type path from body
        const parts = [];
        let current = el;
        while (current && current !== document.body && parts.length < 6) {
            const parent = current.parentElement;
            if (!parent) break;
            const siblings = Array.from(parent.children).filter(
                c => c.tagName === current.tagName
            );
            const tag = current.tagName.toLowerCase();
            if (siblings.length === 1) {
                parts.unshift(tag);
            } else {
                const idx = siblings.indexOf(current) + 1;
                parts.unshift(`${tag}:nth-of-type(${idx})`);
            }
            current = parent;
        }
        return parts.join(' > ');
    }

    function isVisible(el) {
        // Skip SVG internals (path, g, circle, etc.) — they inherit
        // pointer cursor from parent but aren't independently interactive
        const svgInternals = ['PATH','G','CIRCLE','RECT','LINE','POLYGON',
                              'POLYLINE','ELLIPSE','DEFS','CLIPPATH','MASK','USE'];
        if (svgInternals.includes(el.tagName)) return false;

        const style = window.getComputedStyle(el);
        return style.display !== 'none'
            && style.visibility !== 'hidden'
            && style.opacity !== '0'
            && el.offsetWidth > 0
            && el.offsetHeight > 0;
    }

    function isDescendantOfProcessed(el) {
        let parent = el.parentElement;
        while (parent) {
            if (processedEls.has(parent)) return true;
            parent = parent.parentElement;
        }
        return false;
    }

    function describeElement(el) {
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel) return ariaLabel;

        let text = (el.textContent || '').trim().substring(0, 80);
        if (text) return text;

        const title = el.getAttribute('title');
        if (title) return title;
        const placeholder = el.getAttribute('placeholder');
        if (placeholder) return placeholder;
        return el.tagName.toLowerCase();
    }

    // For elements with duplicate labels, add context from the nearest
    // semantic container (article, section, li, fieldset, etc.)
    function disambiguate(el, label) {
        const container = el.closest('article, section, li, fieldset, [role="group"], [role="region"], tr, details');
        if (!container) return label;

        // Find the most descriptive text in the container that isn't the
        // same as our label: headings first, then first link, then first
        // substantial text node
        const heading = container.querySelector('h1, h2, h3, h4, h5, h6');
        if (heading) {
            const ht = heading.textContent.trim().substring(0, 60);
            if (ht && ht !== label) return `${label} (${ht})`;
        }
        const link = container.querySelector('a[href]');
        if (link) {
            const lt = link.textContent.trim().substring(0, 60);
            if (lt && lt !== label) return `${label} (${lt})`;
        }
        const ariaLabel = container.getAttribute('aria-label');
        if (ariaLabel && ariaLabel !== label) {
            return `${label} (${ariaLabel.substring(0, 60)})`;
        }
        return label;
    }

    function classifyAction(el) {
        const tag = el.tagName;
        const role = el.getAttribute('role') || '';
        const href = el.getAttribute('href');

        // Navigation: links, tabs, listitem in a nav-like context
        if (tag === 'A' && href) return 'navigate';
        if (role === 'tab') return 'navigate';
        if (role === 'listitem') {
            const parent = el.closest('[role="list"], [role="tablist"], nav');
            if (parent) return 'navigate';
        }

        // Input
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return 'input';
        if (el.getAttribute('contenteditable') === 'true') return 'input';

        // Default: click
        return 'click';
    }

    // ========================================
    // Phase 1: Standard semantic elements
    // ========================================

    // Links
    document.querySelectorAll('a[href]').forEach(el => {
        if (!isVisible(el)) return;
        const href = el.getAttribute('href');
        if (!href || href === '#' || href.startsWith('javascript:')) return;
        const desc = describeElement(el);
        if (desc.length < 2) return;
        const sel = getSelector(el);
        processedEls.add(el);
        addAction(el, 'navigate', `Navigate: ${desc}`, sel);
    });

    // Buttons (native)
    document.querySelectorAll('button, input[type="button"], input[type="submit"]').forEach(el => {
        if (!isVisible(el)) return;
        const desc = describeElement(el);
        const sel = getSelector(el);
        processedEls.add(el);
        addAction(el, 'click', `Button: ${desc}`, sel);
    });

    // Text inputs
    document.querySelectorAll('input:not([type="button"]):not([type="submit"]):not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), textarea, select').forEach(el => {
        if (!isVisible(el)) return;
        const desc = describeElement(el);
        const sel = getSelector(el);
        processedEls.add(el);
        addAction(el, 'input', `Input: ${desc}`, sel);
    });

    // ========================================
    // Phase 2: ARIA role-based elements
    // ========================================

    const interactiveRoles = [
        'button', 'link', 'tab', 'menuitem', 'menuitemcheckbox',
        'menuitemradio', 'option', 'switch', 'checkbox', 'radio',
        'listitem', 'treeitem', 'gridcell',
    ];

    for (const role of interactiveRoles) {
        document.querySelectorAll(`[role="${role}"]`).forEach(el => {
            if (!isVisible(el) || processedEls.has(el)) return;
            if (isDescendantOfProcessed(el)) return;
            const desc = describeElement(el);
            if (desc.length < 2) return;
            const sel = getSelector(el);
            processedEls.add(el);
            const actionType = classifyAction(el);
            const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);
            addAction(el, actionType, `${roleLabel}: ${desc}`, sel);
        });
    }

    // ========================================
    // Phase 3: Cursor-pointer and tabindex elements
    // (catch custom interactive components)
    // ========================================

    document.querySelectorAll('[tabindex], [onclick]').forEach(el => {
        if (!isVisible(el) || processedEls.has(el)) return;
        if (isDescendantOfProcessed(el)) return;
        const tabindex = el.getAttribute('tabindex');
        if (tabindex === '-1') return;  // programmatic focus only
        const desc = describeElement(el);
        if (desc.length < 2) return;
        const sel = getSelector(el);
        processedEls.add(el);
        const actionType = classifyAction(el);
        addAction(el, actionType, `Interactive: ${desc}`, sel);
    });

    // Cursor-pointer elements that aren't already found
    // (limit to direct text-bearing elements to avoid noise)
    const allEls = document.querySelectorAll('div, span, li, label, summary, details, img');
    for (const el of allEls) {
        if (processedEls.has(el)) continue;
        if (!isVisible(el)) continue;
        if (isDescendantOfProcessed(el)) continue;

        const style = window.getComputedStyle(el);
        if (style.cursor !== 'pointer') continue;

        // Must have direct text content (not just inherited from children)
        // or an aria-label/title
        const ariaLabel = el.getAttribute('aria-label');
        const title = el.getAttribute('title');
        const directText = Array.from(el.childNodes)
            .filter(n => n.nodeType === 3)
            .map(n => n.textContent.trim())
            .join('');
        const hasOwnLabel = ariaLabel || title || directText.length > 2;

        // Also accept img elements with alt text
        if (el.tagName === 'IMG') {
            const alt = el.getAttribute('alt');
            if (alt) {
                const sel = getSelector(el);
                processedEls.add(el);
                addAction(el, 'click', `Image: ${alt}`, sel);
                continue;
            }
        }

        if (!hasOwnLabel) continue;

        // Skip if a child of this element is already interactive
        const hasInteractiveChild = el.querySelector('a, button, [role="button"], [role="tab"], [role="listitem"]');
        if (hasInteractiveChild) continue;

        const desc = describeElement(el);
        if (desc.length < 2) return;
        const sel = getSelector(el);
        processedEls.add(el);
        addAction(el, 'click', `Clickable: ${desc}`, sel);
    }

    // ========================================
    // Phase 4: Disambiguate duplicate labels
    // ========================================

    // Count how many times each description appears
    const descCounts = {};
    for (const a of actions) {
        descCounts[a.description] = (descCounts[a.description] || 0) + 1;
    }

    // For duplicates, add context from nearest semantic container
    for (let i = 0; i < actions.length; i++) {
        if (descCounts[actions[i].description] > 1) {
            const el = actionElements[i];
            actions[i].description = disambiguate(el, actions[i].description);
            actions[i].element_text = disambiguate(el, actions[i].element_text);
        }
    }

    return actions;
}
