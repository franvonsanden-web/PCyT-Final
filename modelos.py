# modelos.py
# Lazy loading para evitar errores de importación en startup

MODEL_DEMUCS = "htdemucs"
MODEL_MUSICGEN = "facebook/musicgen-small"

# -------------------------------------------------------
# CARGA DIFERIDA (lazy loading)
# Solo se cargan cuando se piden por primera vez.
# Después quedan en memoria.
# -------------------------------------------------------

_demucs_model = None
_musicgen_processor = None
_musicgen_model = None


def get_demucs_model():
    """Carga el modelo Demucs solo cuando se necesita"""
    global _demucs_model
    if _demucs_model is None:
        print("⏳ Cargando modelo Demucs (solo la primera vez)...")
        try:
            import torch
            from demucs.pretrained import get_model
            DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
            _demucs_model = get_model(MODEL_DEMUCS).to(DEVICE).eval()
            print("✅ Demucs cargado exitosamente")
        except Exception as e:
            print(f"❌ Error al cargar Demucs: {e}")
            raise
    return _demucs_model


def get_musicgen():
    """Carga MusicGen solo cuando se necesita"""
    global _musicgen_processor, _musicgen_model

    if _musicgen_processor is None or _musicgen_model is None:
        print("⏳ Cargando modelo MusicGen (solo la primera vez)...")
        try:
            import torch
            from transformers import AutoProcessor, MusicgenForConditionalGeneration
            DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
            
            _musicgen_processor = AutoProcessor.from_pretrained(
                MODEL_MUSICGEN,
                force_download=False,      # No fuerza descargas cada vez
                local_files_only=False     # Usa primero cache local
            )
            _musicgen_model = MusicgenForConditionalGeneration.from_pretrained(
                MODEL_MUSICGEN,
                force_download=False,
                local_files_only=False
            ).to(DEVICE)
            print("✅ MusicGen cargado exitosamente")
        except Exception as e:
            print(f"❌ Error al cargar MusicGen: {e}")
            raise
    return _musicgen_processor, _musicgen_model