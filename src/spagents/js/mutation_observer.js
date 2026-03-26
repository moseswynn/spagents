() => {
    if (window.__spagents_observer) return;

    window.__spagents_mutation_count = 0;
    window.__spagents_last_mutation_ts = Date.now();

    const observer = new MutationObserver((mutations) => {
        window.__spagents_mutation_count += mutations.length;
        window.__spagents_last_mutation_ts = Date.now();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        characterData: true
    });

    window.__spagents_observer = observer;
}
