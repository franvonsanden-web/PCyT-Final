Proyecto MusicGenerator – Entregable

1. Introducción
Este proyecto implementa una aplicación web para la generación y el procesamiento de audio basada en inteligencia artificial y señal digital. Permite al usuario subir archivos de audio, aplicar una separación de pistas (“stems”), mezclar pistas resultantes, y descargar el resultado desde una interfaz accesible vía navegador. La aplicación está desarrollada con Python 3 y el micro-framework Flask.

2. Objetivos
Objetivo general
Construir una plataforma funcional que facilite la manipulación automatizada de audio (separación de stems, mezcla de pistas) con una interfaz web intuitiva.
Objetivos específicos
- Implementar la funcionalidad de carga de archivos mediante formulario web.
- Integrar un módulo de procesamiento de audio para separación de stems (separate_stems) y mezcla (mix_tracks).
- Proporcionar rutas web que permitan la descarga del audio resultante.
- Documentar correctamente la instalación, uso y arquitectura del sistema.

3. Arquitectura general
La aplicación consta de los siguientes componentes:
1. Interfaz Web: Formularios HTML que permiten al usuario subir archivo(s) de audio y seleccionar parámetros de procesamiento.
2. Backend Flask: Módulo principal (main.py o similar) que recibe la solicitud, gestiona archivos, invoca los módulos de procesamiento (procesamiento_audio.py) y devuelve el archivo final.
3. Módulos de dominio (clases.py): Definición de clases como ProyectoAudio, Cancion y Pista, que abstraen la lógica de negocio del audio.
4. Procesamiento de audio: Funciones separate_stems y mix_tracks que ejecutan la lógica de análisis y composición de audio.
5. Almacenamiento temporal: Carpeta “uploads/” para archivos recibidos y “output/” (u otro nombre) para archivos generados.

4. Instalación & configuración
Requisitos previos
- Python 3.10 o superior
- pip
- git
- (Opcional) GPU con soporte para aceleración si el procesamiento de stems lo requiere
- FFmpeg (instalado en el sistema) si el procesamiento de audio lo requiere

Instalación
git clone https://github.com/monicadeus/musicgenerator_entregable.git
cd musicgenerator_entregable
pip install -r requirements.txt

Configuración
- Modificar, si es necesario, rutas de subida/resultados en app.py.
- Verificar los permisos de lectura/escritura en las carpetas uploads/ y output/.
- Si se usa GPU o librerías especiales, configurar el entorno apropiado.

5. Uso de la aplicación
Ejecución
python src/main.py
La aplicación se ejecutará en http://127.0.0.1:3838.

Flujo de uso
1. Acceder al formulario web.
2. Subir un archivo de audio (por ejemplo en formato WAV o MP3).
3. Seleccionar opciones de procesamiento: “Separar stems”, “Mezclar pistas”, etc.
4. Hacer clic en “Procesar”.
5. Una vez completado, descargar el archivo resultante desde el enlace provisto.

6. Explicación técnica
Gestión de archivos
Se utiliza Flask para recibir archivos vía request.files y gestionar su almacenamiento temporal con werkzeug.utils.secure_filename a fin de evitar problemas de seguridad.
Separación de stems y mezcla
La función separate_stems extrae las pistas individuales (voz, batería, bajo, etc.). La función mix_tracks combina las pistas procesadas bajo un nuevo patrón o mezcla.
Modelos de dominio
- ProyectoAudio: clase que representa un proyecto completo de procesamiento de audio, gestionando varias canciones o pistas.
- Cancion: representa un archivo de audio original o transformado.
- Pista: representa una subdivisión de la canción (por ejemplo, voz, instrumentos) que puede ser procesada individualmente.

7. Resultados esperados y conclusiones
El sistema permite a usuarios con conocimientos básicos acceder a procesamiento de audio avanzado sin necesidad de programar. Algunas conclusiones preliminares:
- La separación de stems mejora significativamente la flexibilidad de mezcla.
- La modularidad del diseño facilita extensiones futuras (por ejemplo: efectos, mastering automático).
- Limitaciones actuales incluyen requerimientos de hardware para procesamiento pesado y formatos de audio limitados.

8. Futuras extensiones
- Integrar generación automática de melodías/chords (por ejemplo, utilizando IA).
- Añadir interfaz gráfica más elaborada con vistas de mezcla/interfaz de usuario en tiempo real.
- Incorporar plugins VST o exportación directa para estaciones de trabajo de audio.
- Automatizar publicación de resultados en plataformas como Splice o MercadoLibre (en tu caso, considerando integración con tu ecosistema).

9. Bibliografía
- Y.-Y. Yang, M. Hira, Z. Ni et al., “TorchAudio: Building Blocks for Audio and Speech Processing”, arXiv preprint, 2021.
- A. Torfi, “SpeechPy – A Library for Speech Processing and Recognition”, arXiv preprint, 2018.
