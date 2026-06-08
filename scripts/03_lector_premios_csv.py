import sys
import csv
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def procesar_premios_csv():
    # Asumimos que guardarás el archivo exportado en la raíz con este nombre
    ruta_csv = ROOT_DIR / "premios.csv"
    
    if not ruta_csv.exists():
        print(f"❌ Error: No se encuentra el archivo '{ruta_csv.name}' en la raíz del proyecto.")
        print("Exporta tu Google Forms como CSV, renómbralo a 'premios.csv' y ponlo junto a las carpetas.")
        return

    print("--- 🏆 INICIANDO LECTURA DE PREMIOS EXTRA ---")

    # Usamos utf-8-sig para evitar problemas con los caracteres invisibles (BOM) que a veces mete Excel/Google
    with open(ruta_csv, mode='r', encoding='utf-8-sig') as archivo_csv:
        lector = csv.DictReader(archivo_csv)
        cabeceras = lector.fieldnames
        
        # 1. Autodetectar cuál es la columna del nombre del participante
        columna_nombre = None
        for cabecera in cabeceras:
            if "nombre" in cabecera.lower() or "participante" in cabecera.lower():
                columna_nombre = cabecera
                break
                
        if not columna_nombre:
            print("❌ Error: El CSV debe tener una columna llamada 'Nombre' o 'Participante'.")
            print(f"Columnas detectadas: {cabeceras}")
            return

        participantes_procesados = 0

        # 2. Leer fila por fila (cada fila es un participante)
        for fila in lector:
            nombre_crudo = fila.get(columna_nombre, "").strip()
            if not nombre_crudo:
                continue
                
            nombre_limpio = nombre_crudo.lower().replace(' ', '_')
            ruta_participante = ROOT_DIR / "participantes" / nombre_limpio
            
            if not ruta_participante.exists():
                print(f"⚠️ Saltando a '{nombre_crudo}': No se encontró su carpeta en el sistema. (Ejecuta el script 01 primero)")
                continue

            # 3. Construir el diccionario dinámico con TODAS las preguntas que haya
            respuestas_premios = {}
            for pregunta, respuesta in fila.items():
                pregunta_limpia = pregunta.strip()
                
                # Ignoramos la columna del nombre y la marca temporal de Google Forms
                if pregunta_limpia == columna_nombre or "marca temporal" in pregunta_limpia.lower() or "timestamp" in pregunta_limpia.lower():
                    continue
                    
                respuestas_premios[pregunta_limpia] = respuesta.strip()

            # 4. Empaquetar y guardar en su carpeta
            datos_premios = {
                "participante": nombre_crudo,
                "premios_extra": respuestas_premios
            }
            
            ruta_guardado = ruta_participante / "pronosticos" / "premios.json"
            
            with open(ruta_guardado, 'w', encoding='utf-8') as f:
                json.dump(datos_premios, f, ensure_ascii=False, indent=4)
                
            print(f"✅ Premios registrados para: {nombre_crudo} ({len(respuestas_premios)} respuestas)")
            participantes_procesados += 1

    print(f"\n🎉 Proceso completado. Se han actualizado los premios de {participantes_procesados} participantes.")

if __name__ == "__main__":
    procesar_premios_csv()