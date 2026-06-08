import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return {}
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def generar_readme_realidad():
    print("=======================================================")
    print(" 📰 INICIANDO GENERADOR DE RESULTADOS REALES (MARKDOWN) ")
    print("=======================================================")
    
    ruta_jornadas = ROOT_DIR / "config" / "jornadas.json"
    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    ruta_salida = ROOT_DIR / "data" / "resultados" / "README.md"
    
    jornadas = cargar_json(ruta_jornadas)
    realidad = cargar_json(ruta_realidad)
    
    if not jornadas or not realidad:
        print("❌ Error: Faltan archivos base (jornadas.json o realidad_oficial.json).")
        return

    # --- 1. DICCIONARIO PLANO (Para búsqueda ultra-rápida) ---
    dict_reales = {}
    
    # Mapear Fase de Grupos
    for grupo, partidos in realidad.get("fase_grupos", {}).items():
        for p in partidos:
            clave = f"{p['local']}_vs_{p['visitante']}"
            dict_reales[clave] = p
            
    # Mapear Eliminatorias
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p:
                clave = f"ID_{p['id_partido']}"
                dict_reales[clave] = p

    # --- 2. CONSTRUIR EL MARKDOWN CRONOLÓGICO ---
    md = "# 🌍 Resultados Oficiales - Mundial 2026 🌍\n\n"
    md += "Aquí tienes el registro cronológico de lo que ha sucedido realmente en el terreno de juego.\n\n"

    for j_key, partidos_j in jornadas.items():
        md += f"## 📌 {j_key.upper()}\n"
        md += "| Encuentro | Resultado Oficial |\n"
        md += "| :--- | :---: |\n"
        
        for p_jornada in partidos_j:
            # Determinar la clave según estemos en Grupos o Eliminatorias
            if "id_partido" in p_jornada:
                clave = f"ID_{p_jornada['id_partido']}"
                partido_nombre_fallback = f"Eliminatoria #{p_jornada['id_partido']}"
            else:
                clave = f"{p_jornada['local']}_vs_{p_jornada['visitante']}"
                partido_nombre_fallback = f"{p_jornada['local']} vs {p_jornada['visitante']}"
                
            # Extraer los datos de la realidad oficial
            p_real = dict_reales.get(clave)
            
            if p_real:
                # Es vital sacar los nombres de la realidad para las eliminatorias
                # ya que jornadas.json solo sabe el ID_Partido en esas fases.
                local = p_real.get("local", "TBD")
                visitante = p_real.get("visitante", "TBD")
                encuentro = f"**{local}** vs **{visitante}**"
                
                estado = p_real.get("estado", "notstarted")
                if estado == "finished":
                    gl = p_real.get("goles_local", "-")
                    gv = p_real.get("goles_visitante", "-")
                    resultado = f"<span style='color:goldenrod; font-weight:bold;'>{gl} - {gv}</span>"
                else:
                    resultado = "⏳ *Pendiente*"
            else:
                # Si el partido aún no existe en el JSON de SofaScore
                encuentro = f"*{partido_nombre_fallback}*"
                resultado = "⏳ *Pendiente*"
                
            md += f"| {encuentro} | {resultado} |\n"
            
        md += "\n"

    # --- 3. GUARDAR EL ARCHIVO ---
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(md)
        
    print(f"✅ README de Resultados Reales generado con éxito.")
    print(f"💾 Guardado en: {ruta_salida.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    generar_readme_realidad()