// ============================================
// STATE MANAGEMENT
// ============================================

const state = {
    sourceFile: null,
    stems: [],
    droppedStem: null,
    selectedStyles: [],
    isProcessing: false
};

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initializeUpload();
    initializeStemTabs();
    initializeDragAndDrop();
    initializeStyleTags();
    initializeGenerate();
});

// ============================================
// FILE UPLOAD
// ============================================

function initializeUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });

    // Drag and drop for upload
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('audio/')) {
            handleFileUpload(file);
        }
    });
}

async function handleFileUpload(file) {
    // Show waveform container
    document.getElementById('uploadZone').style.display = 'none';
    document.getElementById('waveformContainer').style.display = 'block';
    document.getElementById('sourceActions').style.display = 'flex';
    document.getElementById('sourceFileName').textContent = file.name;

    // Render waveform
    renderWaveform(file, 'sourceWaveform');

    // Upload to server
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();

        // Store the sanitized filename returned by the server
        state.sourceFile = {
            name: data.filename,  // Use server's sanitized filename
            originalName: file.name
        };

        showNotification('File uploaded successfully', 'success');
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Upload failed', 'error');
    }
}

function renderWaveform(file, containerId) {
    const container = document.getElementById(containerId);
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const reader = new FileReader();

    reader.onload = async (e) => {
        try {
            const arrayBuffer = e.target.result;
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

            drawWaveform(container, audioBuffer);
        } catch (error) {
            console.error('Waveform error:', error);
            // Show placeholder
            container.innerHTML = '<div style="color: #737373; display: flex; align-items: center; justify-content: center; height: 100%;">Waveform visualization</div>';
        }
    };

    reader.readAsArrayBuffer(file);
}

function drawWaveform(container, audioBuffer) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    canvas.style.width = '100%';
    canvas.style.height = '100%';

    container.innerHTML = '';
    container.appendChild(canvas);

    const data = audioBuffer.getChannelData(0);
    const step = Math.ceil(data.length / canvas.width);
    const amp = canvas.height / 2;

    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 1;
    ctx.beginPath();

    for (let i = 0; i < canvas.width; i++) {
        const min = Math.min(...data.slice(i * step, (i + 1) * step));
        const max = Math.max(...data.slice(i * step, (i + 1) * step));

        ctx.moveTo(i, (1 + min) * amp);
        ctx.lineTo(i, (1 + max) * amp);
    }

    ctx.stroke();
}

// ============================================
// REPLACE & SEPARATE
// ============================================

document.getElementById('replaceBtn')?.addEventListener('click', () => {
    document.getElementById('uploadZone').style.display = 'block';
    document.getElementById('waveformContainer').style.display = 'none';
    document.getElementById('sourceActions').style.display = 'none';
    state.sourceFile = null;
    state.stems = [];
    renderStems();
});

document.getElementById('separateBtn')?.addEventListener('click', async () => {
    if (!state.sourceFile) return;

    const button = document.getElementById('separateBtn');
    button.disabled = true;
    button.innerHTML = '<span class="loading"></span> Separating...';

    try {
        const response = await fetch('/separar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre: state.sourceFile.name })
        });

        const data = await response.json();

        if (data.pistas) {
            state.stems = Object.entries(data.pistas).map(([name, path]) => ({
                name,
                path,
                type: detectStemType(name)
            }));

            renderStems();
            showNotification('Stems separated successfully', 'success');
        }
    } catch (error) {
        console.error('Separation error:', error);
        showNotification('Separation failed', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = 'Separate Stems';
    }
});

function detectStemType(name) {
    const lower = name.toLowerCase();
    if (lower.includes('drum')) return 'drums';
    if (lower.includes('vocal')) return 'vocals';
    if (lower.includes('bass')) return 'bass';
    return 'other';
}

// ============================================
// STEM TABS
// ============================================

function initializeStemTabs() {
    const tabs = document.querySelectorAll('.stem-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const filter = tab.dataset.filter;
            renderStems(filter);
        });
    });
}

function renderStems(filter = 'all') {
    const grid = document.getElementById('stemsGrid');

    if (state.stems.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🎵</div>
                <p>Processed stems will appear here</p>
            </div>
        `;
        return;
    }

    const filtered = filter === 'all'
        ? state.stems
        : state.stems.filter(s => s.type === filter);

    grid.innerHTML = filtered.map((stem, index) => {
        const waveformId = `waveform-${index}-${Date.now()}`;
        return `
        <div class="stem-item" draggable="true" data-stem='${JSON.stringify(stem)}'>
            <div class="stem-header">
                <button class="stem-play-btn" data-audio="${stem.path}">▶</button>
                <div class="stem-info">
                    <div>
                        <span class="stem-name">${formatStemName(stem.name)}</span>
                        <span class="stem-tag ${stem.type}">${stem.type}</span>
                    </div>
                </div>
            </div>
            <div class="stem-waveform" id="${waveformId}">
                <div class="loading-waveform">Loading waveform...</div>
            </div>
        </div>
    `}).join('');

    // Render waveforms after DOM update
    filtered.forEach((stem, index) => {
        const waveformId = `waveform-${index}-${Date.now()}`; // Note: This ID generation is risky if re-rendered quickly. 
        // Better to use the same logic or data-attributes. 
        // Actually, let's select by the ID we just generated. 
        // Since we are mapping and joining, we can't easily get the ID back unless we store it.
        // Let's use a simpler approach: select all .stem-waveform and iterate.
    });

    // Better approach for waveforms:
    const waveformContainers = grid.querySelectorAll('.stem-waveform');
    waveformContainers.forEach((container, i) => {
        if (filtered[i]) {
            loadAndRenderWaveform(filtered[i], container);
        }
    });

    // Add play functionality
    grid.querySelectorAll('.stem-play-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            playAudio(btn.dataset.audio, btn);
        });
    });

    // Make stems draggable
    grid.querySelectorAll('.stem-item').forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
    });
}

async function loadAndRenderWaveform(stem, container) {
    try {
        const response = await fetch(stem.path);
        if (!response.ok) throw new Error('Network response was not ok');
        const arrayBuffer = await response.arrayBuffer();

        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        drawWaveform(container, audioBuffer);
    } catch (error) {
        console.error('Error loading waveform for', stem.name, error);
        container.innerHTML = '<div style="font-size: 0.8rem; color: #666;">Waveform unavailable</div>';
    }
}

function formatStemName(name) {
    return name.replace(/\.(wav|mp3)$/i, '').replace(/_/g, ' ');
}

let currentAudio = null;
let currentBtn = null;

function playAudio(path, button) {
    if (currentAudio) {
        currentAudio.pause();
        const prevBtn = currentBtn;
        if (prevBtn) prevBtn.textContent = '▶';

        // If clicking the same button, just stop
        if (currentBtn === button) {
            currentAudio = null;
            currentBtn = null;
            return;
        }
    }

    currentAudio = new Audio(path); // Path is already relative URL from backend
    currentBtn = button;

    button.textContent = '⏸';
    currentAudio.play().catch(e => console.error("Error playing audio:", e));

    currentAudio.onended = () => {
        button.textContent = '▶';
        currentAudio = null;
        currentBtn = null;
    };
}

// ============================================
// DRAG AND DROP
// ============================================

function initializeDragAndDrop() {
    const dropZone = document.getElementById('dropZone');

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        const stemData = e.dataTransfer.getData('stem');
        if (stemData) {
            const stem = JSON.parse(stemData);
            handleStemDrop(stem);
        }
    });
}

function handleDragStart(e) {
    e.target.classList.add('dragging');
    const stemData = e.target.dataset.stem;
    e.dataTransfer.setData('stem', stemData);
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleStemDrop(stem) {
    state.droppedStem = stem;

    const dropZone = document.getElementById('dropZone');
    dropZone.innerHTML = `
        <div class="dropped-stem">
            <div class="dropped-stem-icon">🎵</div>
            <div class="dropped-stem-info">
                <div class="dropped-stem-name">${formatStemName(stem.name)}</div>
                <span class="stem-tag ${stem.type}">${stem.type}</span>
            </div>
            <button class="dropped-stem-remove" onclick="removeStem()">✕</button>
        </div>
    `;

    updateGenerateButton();
}

function removeStem() {
    state.droppedStem = null;
    const dropZone = document.getElementById('dropZone');
    dropZone.innerHTML = `
        <div class="drop-zone-icon">+</div>
        <div class="drop-zone-text">Drag stem here</div>
    `;
    updateGenerateButton();
}

// ============================================
// STYLE TAGS
// ============================================

function initializeStyleTags() {
    const tags = document.querySelectorAll('.style-tag');
    tags.forEach(tag => {
        tag.addEventListener('click', () => {
            tag.classList.toggle('selected');

            const style = tag.dataset.style;
            if (state.selectedStyles.includes(style)) {
                state.selectedStyles = state.selectedStyles.filter(s => s !== style);
            } else {
                state.selectedStyles.push(style);
            }

            updateGenerateButton();
        });
    });
}

function updateGenerateButton() {
    const btn = document.getElementById('generateBtn');
    btn.disabled = !state.droppedStem || state.selectedStyles.length === 0;
}

// ============================================
// GENERATE
// ============================================

function initializeGenerate() {
    const btn = document.getElementById('generateBtn');
    btn.addEventListener('click', async () => {
        if (!state.droppedStem || state.selectedStyles.length === 0) return;

        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Generating...';

        try {
            // Call AI generation endpoint
            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stem: state.droppedStem,
                    styles: state.selectedStyles
                })
            });

            const data = await response.json();

            if (data.success) {
                showNotification('New stem generated successfully', 'success');
                // Add generated stem to list
                state.stems.push(data.generatedStem);
                renderStems();
            }
        } catch (error) {
            console.error('Generation error:', error);
            showNotification('Generation failed', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Generate';
        }
    });
}

// ============================================
// NOTIFICATIONS
// ============================================

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // You can add toast notifications here
}
