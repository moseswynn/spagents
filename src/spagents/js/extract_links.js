() => {
    const links = [];
    const seen = new Set();

    document.querySelectorAll('a[href]').forEach(a => {
        const href = a.href;
        const text = a.textContent.trim();

        if (!href || href === '#' || href.startsWith('javascript:')) return;
        if (!text || text.length < 2) return;
        if (seen.has(href)) return;
        seen.add(href);

        // Find parent context (nearest heading or section)
        let context = '';
        let parent = a.parentElement;
        for (let i = 0; i < 5 && parent; i++) {
            const heading = parent.querySelector('h1, h2, h3, h4, h5, h6');
            if (heading && heading !== a && !a.contains(heading)) {
                context = heading.textContent.trim();
                break;
            }
            const section = parent.closest('section, nav, aside, header, footer, main');
            if (section) {
                const label = section.getAttribute('aria-label')
                    || section.querySelector('h1, h2, h3, h4, h5, h6')?.textContent?.trim()
                    || '';
                if (label) {
                    context = label;
                    break;
                }
            }
            parent = parent.parentElement;
        }

        links.push({ text: text.substring(0, 200), url: href, context });
    });

    return links;
}
