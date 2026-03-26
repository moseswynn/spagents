() => {
    const body = document.body;
    if (!body) return { has_content: false, reason: 'no body' };

    const text = body.innerText || '';
    const textLength = text.trim().length;

    // Check for loading indicators
    const loadingSelectors = [
        '[aria-busy="true"]',
        '.spinner', '.loading', '.skeleton', '.loader',
        '[data-loading]', '[data-loading="true"]',
        '.shimmer', '.placeholder-glow',
    ];
    let hasLoadingIndicators = false;
    for (const sel of loadingSelectors) {
        const els = document.querySelectorAll(sel);
        for (const el of els) {
            const style = window.getComputedStyle(el);
            if (style.display !== 'none' && style.visibility !== 'hidden') {
                hasLoadingIndicators = true;
                break;
            }
        }
        if (hasLoadingIndicators) break;
    }

    // Check for links in main content
    const links = body.querySelectorAll('a[href]');
    const meaningfulLinks = Array.from(links).filter(a => {
        const href = a.getAttribute('href');
        return href && href !== '#' && !href.startsWith('javascript:');
    });

    return {
        has_content: textLength > 200 && !hasLoadingIndicators,
        text_length: textLength,
        has_loading_indicators: hasLoadingIndicators,
        meaningful_link_count: meaningfulLinks.length,
    };
}
