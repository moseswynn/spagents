() => {
    const candidates = [];
    const articles = document.querySelectorAll('article, [role="article"]');

    for (const article of articles) {
        const entry = {
            headline: '',
            category: '',
            summary: null,
            url: null,
            source: null,
            location: '',
            expanded: false,
            sources: [],
            highlights: [],
            perspectives: [],
            quotes: [],
            sections: [],
            images: [],
        };

        // --- Headline: first button or heading text ---
        const headlineEl = article.querySelector('button, h1, h2, h3');
        if (headlineEl) {
            entry.headline = headlineEl.textContent.trim();
        }
        if (!entry.headline) continue;

        // --- Check if this article is expanded ---
        // Expanded articles have h3 sections (Sources, Highlights, etc.)
        const h3s = article.querySelectorAll('h3');
        const sectionNames = Array.from(h3s).map(h => h.textContent.trim());
        const isExpanded = sectionNames.some(n =>
            ['Sources', 'Highlights', 'Perspectives', 'Historical background',
             'Technical details', 'Timeline of events', 'Did you know?',
             'Timeline', 'Context', 'Analysis', 'Key facts'].includes(n)
        );
        entry.expanded = isExpanded;

        if (!isExpanded) {
            // Collapsed article card — grab basic info
            const link = article.querySelector('a[href]');
            entry.url = link ? link.href : null;
            const summaryEl = article.querySelector('p');
            entry.summary = summaryEl ? summaryEl.textContent.trim() : null;

            // Category might be in a small label above the headline
            const allText = article.innerText;
            const lines = allText.split('\n').map(l => l.trim()).filter(Boolean);
            if (lines.length > 1 && lines[0].length < 40 && lines[0] === lines[0].toUpperCase()) {
                entry.category = lines[0];
            }

            candidates.push(entry);
            continue;
        }

        // --- Expanded article: extract rich structure ---

        // Category
        const allText = article.innerText;
        const lines = allText.split('\n').map(l => l.trim()).filter(Boolean);
        if (lines.length > 0 && lines[0].length < 40 && lines[0] === lines[0].toUpperCase()) {
            entry.category = lines[0];
        }

        // Summary paragraphs (paragraphs before the first h3)
        const paragraphs = article.querySelectorAll('p');
        const summaryParts = [];
        for (const p of paragraphs) {
            // Stop at the first h3 sibling boundary
            let foundH3Before = false;
            let prev = p;
            while (prev) {
                prev = prev.previousElementSibling;
                if (prev && prev.tagName === 'H3') { foundH3Before = true; break; }
            }
            // Also check if p is a descendant of an element that comes after an h3
            const closestParent = p.parentElement;
            if (closestParent) {
                let sibling = closestParent;
                while (sibling) {
                    sibling = sibling.previousElementSibling;
                    if (sibling && sibling.tagName === 'H3') { foundH3Before = true; break; }
                    if (sibling && sibling.querySelector && sibling.querySelector('h3')) { foundH3Before = true; break; }
                }
            }

            if (!foundH3Before) {
                const text = p.textContent.trim();
                // Skip image captions and metadata-like short text
                if (text.length > 60) {
                    summaryParts.push(text);
                }
            }
        }
        entry.summary = summaryParts.join('\n\n') || null;

        // Location — look for a line with a location marker
        const locationMatch = allText.match(/[📍⊙◎●]\s*(.+)/);
        if (locationMatch) {
            entry.location = locationMatch[1].trim();
        }
        // Also check for elements near location icons
        const locationEls = article.querySelectorAll('[class*="location"], [class*="geo"]');
        if (!entry.location && locationEls.length > 0) {
            entry.location = locationEls[0].textContent.trim();
        }

        // Sources — links with aria-label mentioning "article from"
        const sourceLinks = article.querySelectorAll('a[aria-label*="article from"], a[aria-label*="articles from"]');
        for (const sl of sourceLinks) {
            const label = sl.getAttribute('aria-label') || '';
            const text = sl.textContent.trim();
            const nameMatch = text.match(/^([\w.-]+)/);
            const name = nameMatch ? nameMatch[1] : text;
            const timeMatch = text.match(/(\d+[hd])\s/);
            const countMatch = label.match(/(\d+) articles?/);
            entry.sources.push({
                name,
                url: sl.href,
                time_ago: timeMatch ? timeMatch[1] : '',
                article_count: countMatch ? parseInt(countMatch[1]) : 1,
            });
        }

        // Highlights — h4 elements under the Highlights h3
        const h4s = article.querySelectorAll('h4');
        for (const h4 of h4s) {
            const title = h4.textContent.trim();
            // Get the next sibling paragraph
            let next = h4.nextElementSibling;
            // Walk up if needed
            if (!next) {
                const parent = h4.parentElement;
                if (parent) next = parent.nextElementSibling;
            }
            const text = next ? next.textContent.trim() : '';
            if (title && text) {
                entry.highlights.push({ title, text });
            }
        }

        // Quotes — blockquotes or elements containing quoted text
        const blockquotes = article.querySelectorAll('blockquote, [class*="quote"]');
        for (const bq of blockquotes) {
            const text = bq.textContent.trim();
            if (text.length > 10) {
                entry.quotes.push(text);
            }
        }

        // Named sections (Perspectives, Historical background, etc.)
        for (const h3 of h3s) {
            const heading = h3.textContent.trim();
            if (['Sources', 'Highlights'].includes(heading)) continue;

            // Collect text from siblings until next h3
            let textParts = [];
            let sibling = h3.nextElementSibling;
            while (sibling && sibling.tagName !== 'H3') {
                const sibText = sibling.textContent.trim();
                if (sibText) textParts.push(sibText);
                sibling = sibling.nextElementSibling;
            }
            // If no direct siblings, look inside parent's next siblings
            if (textParts.length === 0) {
                const parent = h3.parentElement;
                if (parent) {
                    let nextParent = parent.nextElementSibling;
                    while (nextParent) {
                        if (nextParent.querySelector('h3')) break;
                        const t = nextParent.textContent.trim();
                        if (t) textParts.push(t);
                        nextParent = nextParent.nextElementSibling;
                    }
                }
            }

            const sectionText = textParts.join('\n');
            if (heading === 'Perspectives') {
                // Parse perspectives: alternating speaker name and text
                const perspLines = sectionText.split('\n').filter(Boolean);
                for (let i = 0; i < perspLines.length - 1; i += 2) {
                    entry.perspectives.push({
                        speaker: perspLines[i],
                        text: perspLines[i + 1] || '',
                    });
                }
            } else if (sectionText) {
                entry.sections.push({ heading, text: sectionText });
            }
        }

        // Image captions
        const figcaptions = article.querySelectorAll('figcaption, [class*="caption"]');
        for (const fc of figcaptions) {
            const text = fc.textContent.trim();
            if (text) entry.images.push(text);
        }

        // First meaningful link as URL
        const firstLink = article.querySelector('a[href^="http"]');
        entry.url = firstLink ? firstLink.href : null;

        candidates.push(entry);
    }

    return candidates;
}
