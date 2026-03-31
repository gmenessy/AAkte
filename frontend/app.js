/**
 * AAkte — Main application logic.
 *
 * Handles file selection, CleanDocs processing, and API communication.
 */

(function () {
    'use strict';

    const uploadInput = document.getElementById('pdf-upload');
    const dropZone = document.getElementById('drop-zone');
    const fileList = document.getElementById('file-list');
    const submitBtn = document.getElementById('submit-btn');
    const tenantInput = document.getElementById('tenant-id');
    const statusSection = document.getElementById('status-section');
    const statusLog = document.getElementById('status-log');

    let selectedFiles = [];

    // --- File selection ---

    uploadInput.addEventListener('change', (e) => {
        addFiles(Array.from(e.target.files));
    });

    // Drag & drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
        addFiles(files);
    });

    function addFiles(files) {
        selectedFiles = selectedFiles.concat(files);
        renderFileList();
        submitBtn.disabled = selectedFiles.length === 0;
    }

    function renderFileList() {
        fileList.innerHTML = selectedFiles.map(f => `
            <div class="file-item">
                <span class="file-name">${f.name}</span>
                <span class="file-size">${(f.size / 1024).toFixed(1)} KB</span>
            </div>
        `).join('');
    }

    // --- Submit ---

    submitBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;

        const tenantId = tenantInput.value.trim() || 'default';
        submitBtn.disabled = true;
        statusSection.hidden = false;
        statusLog.innerHTML = '';

        for (const file of selectedFiles) {
            await processAndUpload(file, tenantId);
        }

        logStatus('Alle Dokumente verarbeitet.', 'success');
        selectedFiles = [];
        fileList.innerHTML = '';
        submitBtn.disabled = true;
    });

    async function processAndUpload(file, tenantId) {
        logStatus(`Verarbeite: ${file.name}...`, 'info');

        try {
            // Run CleanDocs pipeline (mock in Sprint 1)
            const { markdown, metrics } = await CleanDocs.process(file);

            logStatus(`Sende: ${file.name} an Backend...`, 'info');

            const response = await fetch(`/api/v1/dossier/${encodeURIComponent(tenantId)}/documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: file.name,
                    raw_markdown: markdown,
                    metrics: metrics,
                }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.error?.message || `HTTP ${response.status}`);
            }

            const result = await response.json();
            console.log('[AAkte] Ingestion response:', result);
            logStatus(
                `${file.name} — ID: ${result.document_id} | Sprache: ${result.language_detected} | Status: ${result.status}`,
                'success',
            );
        } catch (err) {
            console.error('[AAkte] Upload failed:', err);
            logStatus(`Fehler bei ${file.name}: ${err.message}`, 'error');
        }
    }

    function logStatus(message, level) {
        const el = document.createElement('div');
        el.className = `status-entry ${level}`;
        el.textContent = message;
        statusLog.appendChild(el);
        statusLog.scrollTop = statusLog.scrollHeight;
    }
})();
