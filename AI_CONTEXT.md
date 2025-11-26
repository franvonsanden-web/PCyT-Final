# Music Generator AI - Solo Dev Context

## 1. The "Elevator Pitch"
* **Project:** Music Generator with AI Stem Transformation
* **Goal:** Upload audio → separate into stems (drums/bass/vocals/other) → transform stems with AI style prompts → download results
* **Key Mechanic:** Drag stem to "Create" panel, select style tags (Lofi, Techno, Jazz, etc.), generate AI-transformed version

## 2. Tech Stack (The "No-Go" Zone)
* **Backend:** Flask (Python 3.10)
* **Frontend:** Vanilla JavaScript (NO frameworks - keep it simple)
* **Styling:** Vanilla CSS (dark theme, modern glassmorphism)
* **Audio Processing:** Spleeter (lightweight) - NOT Demucs (too heavy for solo dev)
* **AI Generation:** Placeholder endpoint ready for future API integration
* **Rule:** No React/Vue/Angular. No build tools. Keep dependencies minimal.

## 3. Architecture Memory Bank
**Decisions that are LOCKED IN:**
* ✅ Single-page app - no routing, no multi-page complexity
* ✅ Lazy imports for heavy libraries (torch, demucs, etc.) to prevent startup crashes
* ✅ Server uses `secure_filename()` - client must use server-returned filename, not original
* ✅ State management in vanilla JS object - no Redux/MobX
* ✅ Backend serves static files via Flask - no CDN, no separate static server
* ✅ All file operations go through `clases.py` (ProyectoAudio, Cancion, Pista classes)
* ✅ Separation endpoint: `/separar` - async processing, returns stem paths
* ✅ Generation endpoint: `/generate` - receives stem + styles, returns generated stem

## 4. Active Roadmap
* **Phase:** MVP - Working Prototype
    * [x] Build modern dark-themed UI (3 sections: Source, Stems, Create)
    * [x] Fix Flask startup crashes (lazy imports)
    * [x] File upload + waveform visualization
    * [ ] **CURRENT:** Replace Demucs with Spleeter for stem separation
    * [ ] Wire up drag-and-drop stem workflow
    * [ ] Connect AI generation to real API (Replicate/HuggingFace)
    * [ ] Add progress indicators for long operations
    * [ ] Export/download functionality

## 5. Current Focus (The "Save State")
* **Last edited:** 2025-11-25
* **Status:** 
  - UI is 100% complete and beautiful ✨
  - Server runs without crashes at `localhost:3838`
  - Upload works, waveform renders perfectly
  - Separation endpoint returns 500 due to Demucs complexity
* **Next Step:** 
  - Install Spleeter: `pip install spleeter`
  - Replace `separate_stems()` in `procesamiento_audio.py` with Spleeter API
  - Test full workflow: upload → separate → drag stem → select styles → generate

## 6. Known Issues & Blockers
* ❌ Demucs requires C++ libraries, PyTorch CUDA, heavy dependencies - SKIP IT
* ✅ Spleeter is lighter, Python-only, good enough for prototype
* ⚠️ AI generation endpoint is placeholder - needs real API integration later
* ⚠️ No progress bars yet - user sees "Separating..." but no percentage

## 7. File Structure (What Goes Where)
```
musicgenerator_entregable-main/
├── app.py                    # Flask routes ONLY - no business logic
├── clases.py                 # Data models (ProyectoAudio, Cancion, Pista)
├── procesamiento_audio.py    # Audio processing functions (separate, mix, generate)
├── modelos.py                # Lazy-loaded AI models (Demucs, MusicGen)
├── gestor_archivos.py        # File I/O utilities
├── templates/index.html      # Single-page UI
├── static/
│   ├── style.css            # Dark theme CSS
│   └── app.js               # Vanilla JS - state + DOM manipulation
└── uploads/                 # User-uploaded files
└── outputs_remix/           # Generated stems + mixes
```

## 8. Quick Commands
```bash
# Start server
python app.py

# Install deps
pip install spleeter Flask python-dotenv werkzeug

# Test separation (once Spleeter is integrated)
curl -X POST http://localhost:3838/separar -H "Content-Type: application/json" -d '{"nombre": "test.wav"}'
```

## 9. Design Philosophy
* **Solo dev = speed over perfection**
* **User uploads audio → gets results fast → that's it**
* **No user accounts, no database, no sessions - stateless MVP**
* **If it takes >30 seconds, show progress. If >2 minutes, rethink the approach.**