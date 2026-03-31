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
        uploadInput.value = '';
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
        for (const file of files) {
            const isDuplicate = selectedFiles.some(
                f => f.name === file.name && f.size === file.size
            );
            if (!isDuplicate) {
                selectedFiles.push(file);
            }
        }
        renderFileList();
        submitBtn.disabled = selectedFiles.length === 0;
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        renderFileList();
        submitBtn.disabled = selectedFiles.length === 0;
    }

    function renderFileList() {
        fileList.innerHTML = '';
        selectedFiles.forEach((f, i) => {
            const item = document.createElement('div');
            item.className = 'file-item';

            const name = document.createElement('span');
            name.className = 'file-name';
            name.textContent = f.name;

            const right = document.createElement('span');
            right.className = 'file-meta';

            const size = document.createElement('span');
            size.className = 'file-size';
            size.textContent = formatSize(f.size);

            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn-remove';
            removeBtn.textContent = '\u00d7';
            removeBtn.title = 'Entfernen';
            removeBtn.addEventListener('click', () => removeFile(i));

            right.appendChild(size);
            right.appendChild(removeBtn);
            item.appendChild(name);
            item.appendChild(right);
            fileList.appendChild(item);
        });
    }

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    // --- Submit ---

    submitBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;

        const tenantId = tenantInput.value.trim() || 'default';

        if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(tenantId)) {
            logStatus('Ungueltige Tenant-ID. Nur Buchstaben, Ziffern, Bindestriche und Unterstriche erlaubt.', 'error');
            return;
        }

        submitBtn.disabled = true;
        statusSection.hidden = false;
        statusLog.innerHTML = '';

        const total = selectedFiles.length;
        let completed = 0;
        let errors = 0;

        for (const file of selectedFiles) {
            const ok = await processAndUpload(file, tenantId, completed + 1, total);
            if (ok) {
                completed++;
            } else {
                errors++;
            }
        }

        const summary = errors === 0
            ? `Alle ${total} Dokumente erfolgreich verarbeitet.`
            : `${completed}/${total} erfolgreich, ${errors} fehlgeschlagen.`;
        logStatus(summary, errors === 0 ? 'success' : 'error');

        selectedFiles = [];
        renderFileList();
        submitBtn.disabled = true;
    });

    async function processAndUpload(file, tenantId, current, total) {
        logStatus(`[${current}/${total}] Verarbeite: ${file.name}...`, 'info');

        try {
            const { markdown, metrics } = await CleanDocs.process(file);

            logStatus(`[${current}/${total}] Sende: ${file.name} an Backend...`, 'info');

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
                `[${current}/${total}] ${file.name} — ID: ${result.document_id} | Sprache: ${result.language_detected} | Status: ${result.status}`,
                'success',
            );
            return true;
        } catch (err) {
            console.error('[AAkte] Upload failed:', err);
            logStatus(`[${current}/${total}] Fehler bei ${file.name}: ${err.message}`, 'error');
            return false;
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
