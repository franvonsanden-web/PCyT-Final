import os
import subprocess
from typing import List
from pathlib import Path

# Lazy imports - only when needed
# import numpy as np
# import torch
# import librosa
# import soundfile as sf

# =========================
# GLOBAL SETTINGS
# =========================
SAMPLE_RATE = 32000

def get_device():
    """Get torch device lazily"""
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"

# =========================
# UTILS
# =========================
def log(msg: str):
    """Print to console and write to remix.log"""
    print(msg, flush=True)
    try:
        with open("remix.log", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception as e:
        print(f"No se pudo escribir en log: {e}")


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def save_audio(path, audio, sr=SAMPLE_RATE):
    """Guarda audio en formato WAV"""
    import soundfile as sf
    if audio.ndim > 1:
        audio = audio.T
    sf.write(path, audio, sr)
    log(f"Audio guardado: {path}")


# =========================
# FUNCIONES PRINCIPALES
# =========================

def separate_stems(input_audio, out_dir):
    """
    Separa un archivo de audio en stems usando Demucs.
    
    Args:
        input_audio: Ruta al archivo de audio a separar
        out_dir: Directorio donde guardar los stems
    
    Returns:
        dict: Diccionario con los paths a cada stem {stem_name: path}
              Stems: vocals, drums, bass, other
    
    Raises:
        FileNotFoundError: Si el archivo de entrada no existe
        RuntimeError: Si Demucs falla o no genera los outputs esperados
    """
    if not os.path.exists(input_audio):
        raise FileNotFoundError(f"El archivo no existe: {input_audio}")

    os.makedirs(out_dir, exist_ok=True)

    print("🎵 Iniciando separación de stems con Demucs...")
    print(f"📁 Archivo: {input_audio}")
    print(f"📁 Salida: {out_dir}")

    try:
        # Nombre del archivo sin extensión (para ubicar la carpeta de salida)
        song_name = os.path.splitext(os.path.basename(input_audio))[0]
        
        # Comando Demucs
        # -n htdemucs: usa el modelo pre-entrenado htdemucs (mejor calidad)
        # -o out_dir: directorio de salida
        # --two-stems: Opción comentada por ahora, usa 4 stems por defecto
        command = [
            "demucs",
            "-n", "htdemucs",
            "-o", out_dir,
            input_audio
        ]
        
        print(f"🔧 Ejecutando: {' '.join(command)}")
        
        # Ejecutar Demucs (bloqueante - espera a que termine)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        # Imprimir output de Demucs para debugging
        if stdout:
            print("📋 Output de Demucs:")
            print(stdout)
        
        if process.returncode != 0:
            print(f"❌ Error de Demucs:\n{stderr}")
            raise RuntimeError(f"Demucs falló con código {process.returncode}: {stderr}")
        
        # Demucs guarda en: out_dir/htdemucs/song_name/{vocals,drums,bass,other}.wav
        demucs_output_dir = os.path.join(out_dir, "htdemucs", song_name)
        
        if not os.path.exists(demucs_output_dir):
            raise RuntimeError(
                f"Demucs no generó la carpeta esperada: {demucs_output_dir}"
            )
        
        # Construir diccionario de stems
        stems = {}
        expected_stems = ["vocals", "drums", "bass", "other"]
        
        for stem_name in expected_stems:
            stem_path = os.path.join(demucs_output_dir, f"{stem_name}.wav")
            
            if not os.path.exists(stem_path):
                print(f"⚠️  Stem no encontrado: {stem_name}")
                continue
            
            # Verificar que el archivo no esté vacío
            size = os.path.getsize(stem_path)
            if size < 1000:  # Menos de 1KB probablemente indica error
                print(f"⚠️  Stem {stem_name} muy pequeño ({size} bytes), ignorando")
                continue
            
            stems[stem_name] = stem_path
            print(f"✅ Stem generado: {stem_name} ({size:,} bytes)")
        
        if not stems:
            raise RuntimeError(
                "Demucs se ejecutó pero todos los stems salieron vacíos o no se generaron. "
                "Verifica que el archivo de entrada sea un audio válido."
            )
        
        print(f"🎉 Separación completada exitosamente: {len(stems)} stems")
        return stems
        
    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {e}")
        raise
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando Demucs: {e}")
        raise RuntimeError(f"Error ejecutando Demucs: {e}")
    except Exception as e:
        print(f"❌ Error inesperado en separación: {e}")
        raise


def generate_accompaniment(style_prompt, out_path, duration=10):
    """
    Genera un acompañamiento musical con MusicGen.
    Default duration: 10s
    """
    import torch
    import numpy as np
    from modelos import get_musicgen
    
    DEVICE = get_device()
    musicgen_processor, musicgen_model = get_musicgen()
    
    prompt = f"background music in {style_prompt} style"
    log(f"Generando acompañamiento: {prompt} ({duration}s)")

    try:
        inputs = musicgen_processor(
            text=prompt,
            return_tensors="pt",
            padding=True
        ).to(DEVICE)

        log("Generando audio con MusicGen...")
        with torch.no_grad():
            audio = musicgen_model.generate(
                **inputs,
                max_new_tokens=int(duration * SAMPLE_RATE / 256)
            )

        # Normalizar y guardar
        arr = audio[0, 0].cpu().numpy()
        arr = arr / (np.max(np.abs(arr)) + 1e-9)
        save_audio(out_path, arr, SAMPLE_RATE)
        log(f"Acompañamiento generado → {out_path}")
        return out_path

    except Exception as e:
        log(f"❌ Error en generación: {e}")
        raise


def generate_stem_variation(stem_type: str, style: str, out_path: str, duration: int = 10):
    """
    Genera una variación de un stem usando MusicGen (Text-to-Music).
    Crea un nuevo audio basado en el tipo de instrumento y el estilo.
    """
    import torch
    import numpy as np
    from modelos import get_musicgen
    
    DEVICE = get_device()
    musicgen_processor, musicgen_model = get_musicgen()
    
    # Prompt engineering para aislar el instrumento
    prompt = f"solitary {stem_type} track, {style} style, high quality, loopable, no other instruments"
    log(f"Generando variación: {prompt} ({duration}s)")

    try:
        inputs = musicgen_processor(
            text=prompt,
            return_tensors="pt",
            padding=True
        ).to(DEVICE)

        log("Generando audio con MusicGen...")
        with torch.no_grad():
            audio = musicgen_model.generate(
                **inputs,
                max_new_tokens=int(duration * SAMPLE_RATE / 256)
            )

        # Normalizar y guardar
        arr = audio[0, 0].cpu().numpy()
        arr = arr / (np.max(np.abs(arr)) + 1e-9)
        save_audio(out_path, arr, SAMPLE_RATE)
        log(f"Variación generada → {out_path}")
        return out_path

    except Exception as e:
        log(f"❌ Error en generación de variación: {e}")
        raise


def mix_tracks(track_paths: List[str], out_path: str):
    """
    Mezcla N pistas de audio.
    Normaliza la mezcla final para evitar clipping.
    """
    import librosa
    import numpy as np
    
    log(f"Mezclando {len(track_paths)} pistas...")
    
    if not track_paths:
        raise ValueError("No se proporcionaron pistas para mezclar")

    try:
        loaded_audios = []
        min_len = None

        # 1. Cargar todos los audios
        for path in track_paths:
            y, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
            loaded_audios.append(y)
            if min_len is None or len(y) < min_len:
                min_len = len(y)

        if min_len == 0:
            raise ValueError("Una de las pistas tiene longitud 0")

        # 2. Sumar (recortando al más corto)
        mix = np.zeros(min_len, dtype=np.float32)
        for y in loaded_audios:
            mix += y[:min_len]

        # 3. Normalizar
        max_val = np.max(np.abs(mix))
        if max_val > 0:
            mix = mix / (max_val + 1e-9)

        # 4. Guardar
        save_audio(out_path, mix, SAMPLE_RATE)
        log(f"Mezcla final → {out_path}")
        return out_path

    except Exception as e:
        log(f"❌ Error en mezcla: {e}")
        raise
