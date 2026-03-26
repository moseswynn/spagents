() => {
    // Try to find main content area
    const main = document.querySelector('main, [role="main"], #content, .content, article');
    const target = main || document.body;
    return (target.innerText || '').trim().substring(0, 50000);
}
