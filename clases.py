# clases.py
# Contiene los modelos: Cancion, Pista y ProyectoAudio
# Objetivo: separar la lógica de datos (modelo) del servidor (app.py)

import os
from procesamiento_audio import separate_stems, generate_accompaniment, mix_tracks
from datetime import datetime
from typing import List, Optional
from gestor_archivos import GestorArchivos

class Pista:
    """
    Representa una pista (stem) individual de audio.
    Por ejemplo: voz, guitarra, bajo, batería...
    """
    def __init__(self, nombre: str, archivo_ruta: str, duracion_seg: Optional[float] = None):
        self.nombre = nombre
        self.archivo_ruta = archivo_ruta  # ruta al archivo físico en disco
        self.duracion_seg = duracion_seg  # duración en segundos (si se conoce)
        self.metadatos = {}               # diccionario libre para tags adicionales

    def __repr__(self):
        return f"Pista(nombre={self.nombre}, archivo={os.path.basename(self.archivo_ruta)})"

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "archivo_ruta": self.archivo_ruta,
            "duracion_seg": self.duracion_seg,
            "metadatos": self.metadatos
        }


class Cancion:
    """
    Representa un archivo de canción subido por el usuario.
    Mantiene metadatos básicos y referencia a pistas (si se separó en stems).
    """
    def __init__(self, titulo: str, archivo_ruta: str, formato: Optional[str] = None):
        self.titulo = titulo
        self.archivo_ruta = archivo_ruta
        self.formato = formato or self._infer_format()
        self.tamanio_bytes = self._get_size_bytes()
        self.hora_subida = datetime.now()
        self.pistas: List[Pista] = []  # listas de Pista asociadas tras separación
        self.metadatos = {}            # por ejemplo artista, album, bpm, etc.

    def _infer_format(self) -> Optional[str]:
        """Extrae la extensión del archivo como formato (mp3, wav, ...)."""
        parts = os.path.basename(self.archivo_ruta).rsplit(".", 1)
        return parts[1].lower() if len(parts) == 2 else None

    def _get_size_bytes(self) -> int:
        """Devuelve el tamaño del archivo en bytes (0 si no existe)."""
        try:
            return os.path.getsize(self.archivo_ruta)
        except Exception:
            return 0

    def agregar_pista(self, pista: Pista):
        """Añade una pista a la canción (por ejemplo tras separar stems)."""
        self.pistas.append(pista)

    def reproducir(self):
        print(f"Reproduciendo {self.titulo} desde {self.archivo_ruta}")

    def info_simple(self) -> dict:
        """Devuelve información resumen de la canción (útil para la UI)."""
        return {
            "titulo": self.titulo,
            "archivo": os.path.basename(self.archivo_ruta),
            "formato": self.formato,
            "tam_kb": int(self.tamanio_bytes / 1024),
            "hora_subida": self.hora_subida.isoformat(),
            "num_pistas": len(self.pistas)
        }

    def to_dict(self) -> dict:
        return {
            "titulo": self.titulo,
            "archivo_ruta": self.archivo_ruta,
            "formato": self.formato,
            "tamanio_bytes": self.tamanio_bytes,
            "hora_subida": self.hora_subida.isoformat(),
            "pistas": [p.to_dict() for p in self.pistas],
            "metadatos": self.metadatos
        }

    def __repr__(self):
        return f"Cancion(titulo={self.titulo}, archivo={os.path.basename(self.archivo_ruta)})"

class ProyectoAudio:
    """
    Representa un proyecto que puede contener varias canciones y el estado del
    procesamiento (separación, mezcla, exportación).
    """
    def __init__(self, nombre_proyecto: str):
        self.nombre = nombre_proyecto
        self.canciones: List[Cancion] = []
        self.created_at = datetime.now()
        self.outputs_dir = "outputs_remix"  # carpeta por defecto para resultados
        os.makedirs(self.outputs_dir, exist_ok=True)

    def agregar_cancion(self, cancion):
        """
        Añade una Cancion al proyecto.
        Valida que el objeto sea del tipo correcto antes de agregarlo.
        """
        if not isinstance(cancion, Cancion):
            raise TypeError(f"Se esperaba un objeto Cancion, pero se recibió {type(cancion).__name__}")

        self.canciones.append(cancion)
        return cancion

    def encontrar_cancion_por_archivo(self, filename: str) -> Optional[Cancion]:
        """Busca una canción por nombre de archivo (basename)."""
        for c in self.canciones:
            if os.path.basename(c.archivo_ruta) == filename:
                return c
        return None

    def listar_canciones(self) -> List[dict]:
        """Devuelve una lista con información simple de las canciones del proyecto."""
        return [c.info_simple() for c in self.canciones]

    # Métodos placeholder que la app puede llamar (se recomienda implementar en otro módulo)
    def separar_stems(self):
        return separate_stems(self.cancion.ruta_archivo, self.output_dir)

    def generar_acompanamiento(self, estilo, duracion=30):
        out_path = os.path.join(self.output_dir, "accompaniment_generated.wav")
        return generate_accompaniment(estilo, out_path, duracion)

    def mezclar(self, vocal_wav, accomp_wav):
        out_path = os.path.join(self.output_dir, "final_mix.wav")
        return mix_tracks(vocal_wav, accomp_wav, out_path)

    def guardar_estado(self):
        """Guarda la información completa del proyecto en JSON."""
        gestor = GestorArchivos("estado_proyecto.json")
        data = [c.to_dict() for c in self.canciones]
        gestor.guardar_json(data)

    def cargar_estado(self):
        """Carga canciones previamente guardadas (si existe el JSON)."""
        gestor = GestorArchivos("estado_proyecto.json")
        data = gestor.leer_json()
        if not data:
            raise ValueError("No saved state found")
        
        self.canciones = []
        for c_data in data:
            try:
                # Reconstruir Cancion
                cancion = Cancion(c_data["titulo"], c_data["archivo_ruta"], c_data.get("formato"))
                cancion.tamanio_bytes = c_data.get("tamanio_bytes", 0)
                if "hora_subida" in c_data:
                    cancion.hora_subida = datetime.fromisoformat(c_data["hora_subida"])
                
                # Reconstruir Pistas
                for p_data in c_data.get("pistas", []):
                    pista = Pista(p_data["nombre"], p_data["archivo_ruta"], p_data.get("duracion_seg"))
                    pista.metadatos = p_data.get("metadatos", {})
                    cancion.agregar_pista(pista)
                
                self.canciones.append(cancion)
                print(f"Canción restaurada: {cancion.titulo} con {len(cancion.pistas)} pistas")
            except Exception as e:
                print(f"Error al restaurar canción desde estado: {e}")


'''
lista_canciones = [
    CancionMP3("Jazz Night", "mp3", "archivos/jazz.mp3"),
    CancionWAV("Rock Live", "wav", "archivos/rock.wav"),
]

for c in lista_canciones:
    c.reproducir()
'''
