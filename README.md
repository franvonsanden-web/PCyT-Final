# 🎵 Music Generator & Stem Separator AI

> **Version 2.0** | Powered by **Demucs** & **MusicGen**

Una aplicación web profesional para separar pistas de audio (stems) y generar variaciones musicales utilizando Inteligencia Artificial de última generación.

---

## 🚀 Características Principales

*   **Separación de Stems**: Aísla Voces, Batería, Bajo y Otros instrumentos de cualquier canción usando el modelo **Demucs (Hybrid Transformer)**.
*   **Visualización de Ondas**: Renderizado de formas de onda en tiempo real para cada pista separada.
*   **Generación AI**: Crea nuevas variaciones de stems (ej. "batería estilo techno") usando **Facebook MusicGen**.
*   **Interfaz Moderna**: UI limpia y responsiva diseñada para un flujo de trabajo eficiente.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

1.  **Python 3.10 o superior**: [Descargar Python](https://www.python.org/downloads/)
2.  **FFmpeg**: **CRUCIAL**. El sistema de audio NO funcionará sin esto.
    *   **Windows**: [Guía de instalación](https://www.wikihow.com/Install-FFmpeg-on-Windows)
    *   **Mac**: `brew install ffmpeg`
    *   **Linux**: `sudo apt install ffmpeg`
3.  **Git**: Para clonar el repositorio.

---

## 🛠️ Guía de Instalación Paso a Paso

### 1. Clonar el Repositorio
```bash
git clone https://github.com/franvonsanden-web/PCyT-Final.git
cd PCyT-Final
```

### 2. Crear Entorno Virtual (Recomendado)
Para evitar conflictos con otras librerías de Python:

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias
Instala todas las librerías necesarias (Flask, Torch, Librosa, etc.):
```bash
pip install -r requirements.txt
```
> *Nota: La primera instalación puede tardar unos minutos ya que descargará PyTorch.*

---

## ▶️ Ejecución del Proyecto

1.  Asegúrate de que tu entorno virtual esté activado.
2.  Inicia el servidor Flask:
```bash
python app.py
```
3.  Verás un mensaje indicando que el servidor está corriendo (usualmente en el puerto 3838).
4.  Abre tu navegador y ve a:
    **[http://localhost:3838](http://localhost:3838)**

---

## 🎮 Cómo Usar la Aplicación

### 1. Cargar Audio
*   Arrastra un archivo MP3 o WAV a la zona de "Source Audio".
*   O haz clic para seleccionar un archivo de tu computadora.

### 2. Separar Stems
*   Haz clic en el botón **"Separate Stems"**.
*   Espera a que la AI procese el audio (puede tardar 1-3 minutos dependiendo de tu PC).
*   Verás aparecer 4 pistas: Vocals, Drums, Bass, Other.

### 3. Generar Variaciones (AI)
*   Arrastra uno de los stems generados (ej. "Drums") a la zona de **"Create"** (abajo a la derecha).
*   Selecciona uno o más estilos (ej. "Techno", "Lofi").
*   Haz clic en **"Generate"**.
*   La AI creará una nueva pista basada en ese instrumento y estilo.

---

## ⚠️ Solución de Problemas Comunes

**Error: "FFmpeg no encontrado"**
*   Asegúrate de haber instalado FFmpeg y, lo más importante, de haber **agregado FFmpeg a las Variables de Entorno (PATH)** de tu sistema.
*   Reinicia la terminal después de instalarlo.

**Error de Memoria (CUDA Out of Memory)**
*   Si tienes una tarjeta gráfica NVIDIA pero poca VRAM, Demucs podría fallar.
*   El sistema intentará usar CPU automáticamente si falla CUDA, pero será más lento.

**La UI no carga las ondas**
*   Asegúrate de estar usando un navegador moderno (Chrome, Firefox, Edge).
*   Revisa la consola del navegador (F12) para ver si hay errores de red.

---

## 💻 Tecnologías

*   **Backend**: Flask (Python)
*   **Frontend**: HTML5, CSS3, Vanilla JS
*   **AI Models**:
    *   [Demucs](https://github.com/facebookresearch/demucs) (Separación de fuentes)
    *   [MusicGen](https://huggingface.co/facebook/musicgen-small) (Generación de música)

---
**Desarrollado para PCyT Final**
Por Mónica Deus, Clara Gomez y Francisco Von Sanden
