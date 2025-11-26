import os
import json
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path


class CacheManager:
    """
    Gestiona el cache de stems procesados y provee diagnósticos.
    """
    
    def __init__(self, output_dir: str, estado_path: str):
        self.output_dir = output_dir
        self.estado_path = estado_path
    
    def get_cache_size_mb(self) -> float:
        """Calcula el tamaño total del cache en MB."""
        total_bytes = 0
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    total_bytes += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_bytes / (1024 * 1024)
    
    def list_all_stem_files(self) -> List[str]:
        """Lista todos los archivos de stems en el filesystem."""
        stems = []
        htdemucs_path = os.path.join(self.output_dir, "htdemucs")
        
        if not os.path.exists(htdemucs_path):
            return stems
        
        for song_dir in os.listdir(htdemucs_path):
            song_path = os.path.join(htdemucs_path, song_dir)
            if os.path.isdir(song_path):
                for file in os.listdir(song_path):
                    if file.endswith('.wav'):
                        stems.append(os.path.join(song_path, file))
        
        return stems
    
    def get_referenced_stems(self) -> List[str]:
        """Obtiene lista de stems referenciados en estado_proyecto.json."""
        referenced = []
        
        if not os.path.exists(self.estado_path):
            return referenced
        
        try:
            with open(self.estado_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for cancion in data:
                for pista in cancion.get('pistas', []):
                    referenced.append(pista['archivo_ruta'])
        except Exception as e:
            print(f"Error leyendo estado: {e}")
        
        return referenced
    
    def find_orphaned_stems(self) -> List[str]:
        """Encuentra stems huérfanos (en disco pero no en estado)."""
        all_stems = set(self.list_all_stem_files())
        referenced = set(self.get_referenced_stems())
        orphaned = all_stems - referenced
        return list(orphaned)
    
    def cleanup_orphaned_stems(self) -> Tuple[int, List[str]]:
        """
        Elimina stems huérfanos del filesystem.
        
        Returns:
            Tuple[int, List[str]]: (cantidad eliminada, lista de rutas eliminadas)
        """
        orphaned = self.find_orphaned_stems()
        deleted = []
        
        for stem_path in orphaned:
            try:
                os.remove(stem_path)
                deleted.append(stem_path)
                print(f"🗑️  Eliminado: {stem_path}")
            except Exception as e:
                print(f"⚠️  Error al eliminar {stem_path}: {e}")
        
        # Cleanup empty directories
        htdemucs_path = os.path.join(self.output_dir, "htdemucs")
        if os.path.exists(htdemucs_path):
            for song_dir in os.listdir(htdemucs_path):
                song_path = os.path.join(htdemucs_path, song_dir)
                if os.path.isdir(song_path) and not os.listdir(song_path):
                    os.rmdir(song_path)
                    print(f"🗑️  Carpeta vacía eliminada: {song_path}")
        
        return len(deleted), deleted
    
    def generate_report(self) -> Dict:
        """
        Genera un reporte completo del estado del cache.
        
        Returns:
            Dict con métricas y estadísticas
        """
        all_stems = self.list_all_stem_files()
        referenced = self.get_referenced_stems()
        orphaned = self.find_orphaned_stems()
        
        # Load estado for counting songs
        total_songs = 0
        total_stems_in_state = 0
        try:
            with open(self.estado_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_songs = len(data)
                for cancion in data:
                    total_stems_in_state += len(cancion.get('pistas', []))
        except:
            pass
        
        # Calculate cache hit rate (stems in state vs total filesystem stems)
        cache_hit_rate = (len(referenced) / len(all_stems)) if all_stems else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "cache_size_mb": round(self.get_cache_size_mb(), 2),
            "total_songs": total_songs,
            "total_stems_in_filesystem": len(all_stems),
            "total_stems_in_state": total_stems_in_state,
            "orphaned_stems": len(orphaned),
            "orphaned_files": orphaned,
            "cache_utilization_rate": round(cache_hit_rate, 3),
            "output_directory": self.output_dir
        }
        
        return report
    
    def rebuild_index(self, proyecto) -> Tuple[int, int]:
        """
        Reconstruye el índice verificando integridad de todas las canciones.
        
        Args:
            proyecto: Instancia de ProyectoAudio
            
        Returns:
            Tuple[int, int]: (canciones actualizadas, pistas eliminadas)
        """
        from procesamiento_audio import validate_stems_integrity
        
        updated_songs = 0
        removed_tracks = 0
        
        for cancion in proyecto.canciones:
            if cancion.pistas:
                stems_dict = {p.nombre: p.archivo_ruta for p in cancion.pistas}
                is_valid, missing = validate_stems_integrity(stems_dict)
                
                if not is_valid:
                    print(f"⚠️  {cancion.titulo}: {len(missing)} pistas inválidas")
                    # Remove invalid tracks
                    valid_pistas = []
                    for pista in cancion.pistas:
                        if os.path.exists(pista.archivo_ruta) and os.path.getsize(pista.archivo_ruta) > 1000:
                            valid_pistas.append(pista)
                        else:
                            removed_tracks += 1
                    
                    cancion.pistas = valid_pistas
                    updated_songs += 1
        
        if updated_songs > 0:
            proyecto.guardar_estado()
            print(f"✅ Índice reconstruido: {updated_songs} canciones actualizadas")
        
        return updated_songs, removed_tracks


# Diagnostics helper
def get_diagnostics(output_dir: str, estado_path: str) -> Dict:
    """
    Función helper para obtener diagnósticos rápidos.
    """
    manager = CacheManager(output_dir, estado_path)
    return manager.generate_report()
