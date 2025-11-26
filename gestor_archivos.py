import json
import os

#=== CLASE GESTORARCHIVOS ===
class GestorArchivos:
    """
        Clase auxiliar para guardar y cargar datos en formato JSON.
        Se usa principalmente por ProyectoAudio para guardar el estado del proyecto.
        """

    def __init__(self, ruta_archivo):
        self.ruta_archivo = ruta_archivo

    def guardar_json(self, datos):
        """Guarda los datos (listas o diccionarios) en un archivo JSON."""
        try:
            with open(self.ruta_archivo, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, indent=2, ensure_ascii=False)
            print(f"✅ Datos guardados correctamente en {self.ruta_archivo}")
        except Exception as e:
            print(f"❌ Error al guardar JSON: {e}")

    def leer_json(self):
        """Lee el JSON del archivo y devuelve los datos."""
        if not os.path.exists(self.ruta_archivo):
            print(f"⚠️ Archivo {self.ruta_archivo} no encontrado.")
            return None
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except json.JSONDecodeError:
            print(f"❌ Error: El archivo {self.ruta_archivo} no contiene JSON válido.")
            return None
        except Exception as e:
            print(f"❌ Error al leer JSON: {e}")
            return None


'''
# === ARCHIVO JSON COMPLETO (con proyecto, canciones y pistas) ===
datos_proyecto_completo = {
    "nombre_proyecto": "Mi Proyecto Musical",
    "canciones": [
        {
            "nombre": "Summer Vibes",
            "formato": "mp3", 
            "ruta_archivo": "/audio/summer_vibes.mp3",
            "pistas": [
                {"tipo": "Voz Principal", "ruta_archivo": "/pistas/voz.wav"},
                {"tipo": "Batería", "ruta_archivo": "/pistas/drums.wav"},
                {"tipo": "Bajo", "ruta_archivo": "/pistas/bass.wav"}
            ]
        },
        {
            "nombre": "Rock Session", 
            "formato": "wav",
            "ruta_archivo": "/audio/rock_session.wav", 
            "pistas": [
                {"tipo": "Guitarra", "ruta_archivo": "/pistas/guitar.wav"},
                {"tipo": "Voz", "ruta_archivo": "/pistas/voz_rock.wav"}
            ]
        }
    ]
}

# === CÓDIGO QUE CONECTA TODO ===
def demo_completa():
    print("🚀 DEMO COMPLETA: Conexión Moni-Cla")
    print("=" * 55)
    
    #Crear el JSON con GestorArchivos
    GestorArchivos.escribir_json(datos_proyecto_completo, 'proyecto_musical.json')
    print("JSON creado por Cla (GestorArchivos)")

    proyecto_cargado = GestorArchivos.cargar_proyecto_desde_json('proyecto_musical.json')
    
    if proyecto_cargado:
        print("Proyecto cargado usando clases de Moni")
        print("\n" + "=" * 55)
        
        # 3. MONI'S PARTE: Mostrar usando los __str__ de Moni
        print("📊 VISUALIZACIÓN (usando métodos de Moni):")
        print("=" * 55)
        print(proyecto_cargado)  # ¡Esto usa el __str__ de ProyectoAudio de Moni!
        
        print("\n" + "=" * 55)
        print("🎯 RESUMEN DE LA CONEXIÓN:")
        print("- Cla: GestorArchivos lee/escribe JSON")
        print("- Moni: Clases Cancion, Pista, ProyectoAudio")  
        print("- Conexión: GestorArchivos CREA objetos de las clases de Moni")
        print("- Resultado: JSON → Objetos → Visualización en consola")
    else:
        print("❌ Error al cargar el proyecto")

# Ejecutar la demo
if __name__ == "__main__":
    demo_completa()
    
Inicialmente se propuso el uso de archivos JSON para simular la estructura del proyecto. 
Finalmente se decidió mantener los archivos en su formato original, pero se conserva la clase
GestorArchivos como herramienta auxiliar para guardar el estado del proyecto.
'''