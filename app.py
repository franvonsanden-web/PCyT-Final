import os
from flask import Flask, request, jsonify, render_template, send_from_directory, flash, redirect, url_for
# from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from os.path import basename
from clases import ProyectoAudio, Cancion, Pista
from procesamiento_audio import separate_stems, mix_tracks, generate_stem_variation, compute_file_hash, validate_stems_integrity
import time

# -------------------------------------------------------
# -------------------------------------------------------
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key_fallback")
# csrf = CSRFProtect(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs_remix"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Proyecto principal de audio
proyecto = ProyectoAudio("Proyecto de Audio")
try:
    proyecto.cargar_estado()
except ValueError:
    print("No se encontró estado previo, iniciando proyecto vacío.")
except Exception as e:
    print(f"Error al cargar estado: {e}")

# Verificar que FFmpeg esté disponible (requerido por Demucs)
def check_ffmpeg():
    """Verifica que FFmpeg esté instalado y disponible"""
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ FFmpeg detectado correctamente")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("=" * 60)
    print("⚠️  ADVERTENCIA: FFmpeg no está instalado")
    print("   Demucs requiere FFmpeg para funcionar.")
    print("   Descarga: https://ffmpeg.org/download.html")
    print("=" * 60)
    return False

check_ffmpeg()

print("Servidor Flask iniciado correctamente")


# -------------------------------------------------------
# Rutas del sistema
# -------------------------------------------------------

@app.route("/")
def index():
    """Página principal (interfaz del usuario)."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Sube un archivo musical y lo registra en el proyecto.
    Si el archivo ya existe (por hash), devuelve el estado guardado."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No se envió ningún archivo"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Nombre de archivo inválido"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        print(f"📁 Archivo guardado: {filepath}")
        
        # ============================================
        # HASH-BASED FILE RECOGNITION
        # ============================================
        file_hash = compute_file_hash(filepath)
        print(f"🔑 Hash SHA-256: {file_hash[:16]}...")
        
        # Check if we've seen this file before
        cancion_existente = proyecto.encontrar_cancion_por_hash(file_hash)
        
        if cancion_existente:
            print(f"♻️ ARCHIVO RECONOCIDO: {filename}")
            print(f"   Canción existente: {cancion_existente.titulo}")
            print(f"   Pistas guardadas: {len(cancion_existente.pistas)}")
            
            # Validate source file still exists
            if not os.path.exists(cancion_existente.archivo_ruta):
                print(f"⚠️ Archivo original eliminado, actualizando ruta")
                cancion_existente.archivo_ruta = filepath
                proyecto.guardar_estado()
            
            # Validate stems integrity
            stems_dict = {p.nombre: p.archivo_ruta for p in cancion_existente.pistas}
            is_valid, missing = validate_stems_integrity(stems_dict)
            
            if not is_valid:
                print(f"⚠️ Integridad comprometida: {missing}")
                print(f"   Se requerirá re-separación")
                restored_stems = []
            else:
                # Deduplicate pistas by nombre (stem type)
                seen_stems = set()
                unique_pistas = []
                for pista in cancion_existente.pistas:
                    if pista.nombre not in seen_stems:
                        unique_pistas.append(pista)
                        seen_stems.add(pista.nombre)
                    else:
                        print(f"⚠️ Pista duplicada ignorada: {pista.nombre}")
                
                # Update if we found duplicates
                if len(unique_pistas) < len(cancion_existente.pistas):
                    cancion_existente.pistas = unique_pistas
                    proyecto.guardar_estado()
                    print(f"🧹 Duplicados eliminados: {len(cancion_existente.pistas) - len(unique_pistas)}")
                
                # Convert to frontend-friendly format
                restored_stems = []
                for pista in unique_pistas:
                    rel_path = os.path.relpath(pista.archivo_ruta, app.config["OUTPUT_FOLDER"])
                    rel_path_url = rel_path.replace(os.sep, '/')
                    restored_stems.append({
                        "name": pista.nombre,
                        "path": f"outputs_remix/{rel_path_url}",
                        "type": pista.nombre  # vocals, drums, bass, other
                    })
                
                print(f"✅ {len(restored_stems)} stems restaurados")
            
            return jsonify({
                "success": True,
                "filename": filename,
                "mensaje": "Archivo reconocido, estado restaurado",
                "restored": True,
                "stems": restored_stems,
                "file_hash": file_hash
            })

        # ============================================
        # NEW FILE - CREATE ENTRY
        # ============================================
        print(f"✨ ARCHIVO NUEVO: {filename}")
        
        # Crear objeto Cancion con hash
        nueva_cancion = Cancion(filename, filepath, "audio", file_hash)

        # Añadir al proyecto
        proyecto.agregar_cancion(nueva_cancion)
        proyecto.guardar_estado()

        print(f"Canción registrada: {filename}")

        return jsonify({
            "success": True,
            "filename": filename,
            "mensaje": "Archivo subido exitosamente",
            "restored": False,
            "file_hash": file_hash
        })

    except Exception as e:
        print(f"Error al subir archivo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al subir archivo: {str(e)}"}), 500


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Sirve archivos subidos"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/proyecto")
def proyecto_view():
    """Muestra la vista del proyecto con la canción seleccionada"""
    nombre_archivo = request.args.get("archivo")
    print(f"🔍 Buscando canción: {nombre_archivo}")

    # Buscar canción en el proyecto
    cancion = proyecto.encontrar_cancion_por_archivo(nombre_archivo)

    if not cancion:
        flash("Canción no encontrada")
        return redirect(url_for("upload_file"))

    print(f"Canción encontrada: {cancion.titulo}")

    return render_template(
        "proyectos.html",
        cancion=cancion,
        archivo=basename(cancion.archivo_ruta)
    )


@app.route("/separar", methods=["POST"])
def separar():
    """
    Separa una canción en stems usando Demucs.
    Inteligente: retorna stems cacheados si existen y son válidos.
    """
    print("Endpoint /separar llamado")

    data = request.get_json()
    nombre_archivo = data.get("nombre")

    print(f"Data recibida: {data}")

    if not nombre_archivo:
        return jsonify({"error": "Falta el nombre del archivo"}), 400

    if not nombre_archivo.lower().endswith(('.mp3', '.wav')):
         return jsonify({"error": "Formato de archivo no soportado (solo .mp3 y .wav)"}), 400

    ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], nombre_archivo)

    # Verificar que el archivo existe
    if not os.path.exists(ruta_archivo):
        print(f"Archivo no encontrado: {ruta_archivo}")
        return jsonify({"error": f"Archivo no encontrado: {nombre_archivo}"}), 404

    # Verificar que el archivo NO esté vacío
    size = os.path.getsize(ruta_archivo)
    print(f"Tamaño del archivo original: {size} bytes")

    if size == 0:
        return jsonify({"error": "El archivo subido está vacío"}), 400

    # Localizar la Cancion en el proyecto
    cancion = proyecto.encontrar_cancion_por_archivo(nombre_archivo)
    if not cancion:
        print(f"Canción no registrada: {nombre_archivo}")
        return jsonify({"error": "Canción no registrada en el proyecto"}), 404

    try:
        # ============================================
        # CHECK FOR CACHED STEMS IN PROJECT STATE
        # ============================================
        if cancion.pistas:
            print(f"🔍 Chequeando {len(cancion.pistas)} stems guardados...")
            
            stems_dict = {p.nombre: p.archivo_ruta for p in cancion.pistas}
            is_valid, missing = validate_stems_integrity(stems_dict)
            
            if is_valid:
                print(f"⚡ CACHE_HIT: Stems válidos encontrados en proyecto")
                
                # Convert to public URLs
                pistas_publicas = {}
                for pista in cancion.pistas:
                    rel_path = os.path.relpath(pista.archivo_ruta, app.config["OUTPUT_FOLDER"])
                    rel_path_url = rel_path.replace(os.sep, '/')
                    pistas_publicas[pista.nombre] = f"outputs_remix/{rel_path_url}"
                    print(f"   ✅ {pista.nombre}")
                
                return jsonify({
                    "mensaje": "Stems recuperados del cache",
                    "pistas": pistas_publicas,
                    "cached": True
                })
            else:
                print(f"⚠️ INTEGRITY_FAIL: {missing}")
                print(f"   Limpiando estado y re-procesando...")
                cancion.pistas = []  # Clear invalid stems
        
        # ============================================
        # CACHE MISS OR INTEGRITY FAIL - RUN DEMUCS
        # ============================================
        print(f"❌ CACHE_MISS: Ejecutando separación...")
        print(f"Archivo: {ruta_archivo}")
        print(f"Output: {app.config['OUTPUT_FOLDER']}")

        # separate_stems now has internal caching for filesystem
        stems = separate_stems(ruta_archivo, app.config["OUTPUT_FOLDER"])

        # VALIDACIÓN: asegurarse de que los stems existen y NO están vacíos
        stems_validos = {}
        for name, path in stems.items():
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                stems_validos[name] = path
                print(f"Pista válida: {name} ({os.path.getsize(path)} bytes)")
            else:
                print(f"⚠️ Pista inválida o vacía: {name} ({os.path.getsize(path) if os.path.exists(path) else 0} bytes)")

        if not stems_validos:
            return jsonify({
                "error": "La separación se ejecutó pero todos los stems están vacíos",
                "detalle": "Revisa separate_stems(): no está esperando a que Demucs escriba."
            }), 500

        # Añadir cada pista válida al proyecto (actualizar estado)
        cancion.pistas = []  # Clear old stems
        for name, path in stems_validos.items():
            pista = Pista(name, path)
            cancion.agregar_pista(pista)
            print(f"Pista añadida al proyecto: {name}")

        proyecto.guardar_estado()

        # Convertir a rutas públicas
        pistas_publicas = {}
        for name, path in stems_validos.items():
            rel_path = os.path.relpath(path, app.config["OUTPUT_FOLDER"])
            rel_path_url = rel_path.replace(os.sep, '/')
            pistas_publicas[name] = f"outputs_remix/{rel_path_url}"

        return jsonify({
            "mensaje": "Separación completada exitosamente",
            "pistas": pistas_publicas,
            "cached": False
        })

    except Exception as e:
        import traceback
        print(f"ERROR DURANTE LA SEPARACIÓN:")
        print(traceback.format_exc())
        return jsonify({
            "error": f"Error durante la separación: {str(e)}",
            "detalle": traceback.format_exc()
        }), 500



@app.route("/mezclar", methods=["POST"])
def mezclar():
    """
    Mezcla pistas (stems) seleccionadas.
    """
    print("Endpoint /mezclar llamado")

    data = request.get_json()
    pistas = data.get("pistas")

    if not pistas or not isinstance(pistas, (list, tuple)):
        return jsonify({"error": "No se proporcionaron pistas en formato lista"}), 400

    try:
        print(f"   Iniciando mezcla de {len(rutas_pistas)} pistas...")
        
        # Llamada SÍNCRONA
        mix_tracks(rutas_pistas, ruta_salida)

        print(f"Mezcla completada: {ruta_salida}")

        return jsonify({
            "mensaje": "Mezcla completada exitosamente",
            "archivo_resultante": basename(ruta_salida)
        })

    except Exception as e:
        import traceback
        print(f"ERROR DURANTE LA MEZCLA:")
        print(traceback.format_exc())
        return jsonify({
            "error": f"Error durante la mezcla: {str(e)}",
            "detalle": traceback.format_exc()
        }), 500


@app.route("/outputs_remix/<path:filename>")
def resultados(filename):
    """Sirve los archivos generados (stems o mezclas)."""
    try:
        return send_from_directory(app.config["OUTPUT_FOLDER"], filename)
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado"}), 404


@app.route("/generate", methods=["POST"])
def generate():
    """
    Genera un nuevo stem usando AI basado en el stem original y estilos seleccionados.
    """
    print("Endpoint /generate llamado")
    
    data = request.get_json()
    stem = data.get("stem")
    styles = data.get("styles", [])
    
    if not stem or not styles:
        return jsonify({"error": "Faltan datos: stem o estilos"}), 400
    
    try:
        print(f"🎨 Generando stem con estilos: {', '.join(styles)}")
        print(f"📁 Stem base: {stem['name']}")
        
        # Generar nombre único
        timestamp = int(time.time())
        style_str = "_".join(styles).replace(" ", "_")
        stem_name_base = os.path.splitext(stem['name'])[0]
        new_filename = f"gen_{stem_name_base}_{style_str}_{timestamp}.wav"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], new_filename)
        
        # Ejecutar generación (síncrona por ahora)
        # Usamos el primer estilo como prompt principal
        main_style = styles[0]
        generate_stem_variation(stem['type'], main_style, output_path)
        
        # Construir respuesta
        generated_stem = {
            "name": new_filename,
            "path": f"outputs_remix/{new_filename}",
            "type": stem["type"],
            "styles": styles
        }
        
        return jsonify({
            "success": True,
            "mensaje": f"Stem generado con estilo: {main_style}",
            "generatedStem": generated_stem
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR DURANTE LA GENERACIÓN:")
        print(traceback.format_exc())
        return jsonify({
            "error": f"Error durante la generación: {str(e)}",
            "detalle": traceback.format_exc()
        }), 500


# -------------------------------------------------------
# Cache & Diagnostics
# -------------------------------------------------------

@app.route("/api/diagnostics")
def diagnostics():
    """
    Provee diagnósticos del cache y estado del sistema.
    """
    from cache_manager import get_diagnostics
    
    try:
        report = get_diagnostics(app.config["OUTPUT_FOLDER"], "estado_proyecto.json")
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cache/cleanup", methods=["POST"])
def cleanup_cache():
    """
    Limpia stems huérfanos (no referenciados en estado_proyecto.json).
    Requiere confirmación explícita del usuario.
    """
    from cache_manager import CacheManager
    
    try:
        manager = CacheManager(app.config["OUTPUT_FOLDER"], "estado_proyecto.json")
        count, deleted = manager.cleanup_orphaned_stems()
        
        return jsonify({
            "success": True,
            "deleted_count": count,
            "deleted_files": deleted
        })
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# -------------------------------------------------------
# Ejecución del servidor
# -------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Servidor de Audio Remix")
    print("=" * 60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"Canciones en proyecto: {len(proyecto.canciones)}")
    print("=" * 60)

    # Ejecutar servidor
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=3838)
