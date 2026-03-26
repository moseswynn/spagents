() => {
    const meta = {};

    // OG tags
    document.querySelectorAll('meta[property^="og:"]').forEach(el => {
        const key = el.getAttribute('property');
        meta[key] = el.getAttribute('content');
    });

    // Standard meta
    const desc = document.querySelector('meta[name="description"]');
    if (desc) meta['description'] = desc.getAttribute('content');

    // Title
    meta['title'] = document.title;

    return meta;
}
