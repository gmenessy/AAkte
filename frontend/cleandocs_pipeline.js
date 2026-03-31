/**
 * CleanDocs v2 Pipeline — Browser-side PDF text reduction.
 *
 * Sprint 1: Mock implementation that generates placeholder Markdown and metrics.
 * Sprint 2: Full implementation with pdf.js, TextRank, SimHash.
 */

const CleanDocs = {
    /**
     * Process a PDF file and return cleaned Markdown with metrics.
     * @param {File} file - The PDF file to process.
     * @returns {Promise<{markdown: string, metrics: object}>}
     */
    async process(file) {
        // Sprint 1: Mock — generate placeholder data from filename
        // Sprint 2: Replace with real pdf.js parsing + TextRank + SimHash
        console.log(`[CleanDocs] Processing: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 300));

        const mockParagraphs = Math.floor(file.size / 500) || 10;
        const removedBoilerplate = Math.floor(mockParagraphs * 0.18);
        const simhashRemoved = Math.floor(mockParagraphs * 0.08);
        const retained = mockParagraphs - removedBoilerplate - simhashRemoved;
        const originalChars = file.size;
        const reducedChars = Math.floor(originalChars * 0.42);

        const markdown = [
            `# ${file.name.replace('.pdf', '')}`,
            '',
            `Dieses Dokument wurde aus der Datei **${file.name}** extrahiert.`,
            '',
            '## Zusammenfassung',
            '',
            'Dies ist ein Platzhalter fuer den bereinigten Dokumenteninhalt.',
            'Die vollstaendige CleanDocs v2 Pipeline wird in Sprint 2 implementiert.',
            '',
            `Originaldateigroesse: ${(file.size / 1024).toFixed(1)} KB`,
        ].join('\n');

        const metrics = {
            original_paragraphs: mockParagraphs,
            removed_boilerplate: removedBoilerplate,
            textrank_retained: retained,
            simhash_removed: simhashRemoved,
            original_chars: originalChars,
            reduced_chars: reducedChars,
            reduction_ratio: parseFloat((1 - reducedChars / originalChars).toFixed(3)),
        };

        console.log('[CleanDocs] Metrics:', metrics);
        return { markdown, metrics };
    },
};
