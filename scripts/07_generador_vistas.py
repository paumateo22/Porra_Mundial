import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def generar_readme_global():
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    if not ruta_csv.exists():
        print("❌ Error: No existe el ranking_oficial.csv.")
        return False

    jornadas_ruta = ROOT_DIR / "config" / "jornadas.json"
    jornadas_dict = cargar_json(jornadas_ruta) or {}
    jornadas_keys = list(jornadas_dict.keys())

    ranking = []
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ranking.append(row)

    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")

    # --- 1. CONSTRUIR CABECERAS DE LA TABLA ---
    headers = ["Pos", "Jugador"] + jornadas_keys + ["Pts Sorpresa", "Pts Decepción", "Premios", "TOTAL"]
    
    md = f"""# 🏆 Clasificación Oficial - Porra Mundial 2026 🏆
    
*Última actualización: {fecha_act}*

Bienvenidos al panel oficial de la Porra. Aquí podéis consultar la clasificación general en tiempo real. 
El formato de las jornadas es **Exactos/1x2**. Los colores indican: <span style="color:goldenrod">**Ganador**</span> de la jornada y <span style="color:red">**Perdedor**</span>.

### 📊 Ranking General

"""
    # Filas de Markdown para la cabecera
    md += "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join([":---:" if h != "Jugador" else ":---" for h in headers]) + " |\n"

    # --- 2. RELLENAR LA TABLA JUGADOR POR JUGADOR ---
    for jug in ranking:
        nombre_id = jug['Jugador'].replace(' ', '_').lower()
        ruta_libro = ROOT_DIR / "participantes" / nombre_id / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro) or {}
        
        # Medallas para el podio
        pos = jug['Posicion']
        if pos == "1": pos = "🥇 1º"
        elif pos == "2": pos = "🥈 2º"
        elif pos == "3": pos = "🥉 3º"
        else: pos = f"{pos}º"

        nombre = f"**[{jug['Jugador']}](participantes/{nombre_id}/README.md)**"
        
        # Procesar Jornadas
        jornadas_columnas = []
        desglose_j = libro.get("desglose_jornadas", {})
        desglose_p = libro.get("desglose_partidos", {})
        
        for j_key in jornadas_keys:
            info_j = desglose_j.get(j_key)
            if not info_j:
                jornadas_columnas.append("-")
                continue
                
            # Calcular aciertos exactos de esta jornada
            exactos = 0
            partidos_de_esta_jornada = jornadas_dict.get(j_key, [])
            for p in partidos_de_esta_jornada:
                # La clave puede ser por ID (eliminatorias) o por Nombre (grupos)
                clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                if desglose_p.get(clave, {}).get("acierto_exacto", False):
                    exactos += 1
            
            aciertos_1x2 = info_j.get("aciertos_1x2", 0)
            texto_celda = f"{exactos}/{aciertos_1x2}"
            resultado = info_j.get("resultado", "")
            
            # Aplicar colores HTML
            if resultado == "Ganador":
                texto_celda = f'<span style="color:goldenrod; font-weight:bold;">{texto_celda}</span>'
            elif resultado == "Perdedor":
                texto_celda = f'<span style="color:red; font-weight:bold;">{texto_celda}</span>'
                
            jornadas_columnas.append(texto_celda)

        # Procesar Premios Extra (Sorpresa, Decepción y Totales Extra)
        premios = libro.get("premios_finales", {})
        forms = premios.get("formularios", {})
        detalles_forms = forms.get("detalles", {})
        
        pts_sorpresa = detalles_forms.get("sorpresa", 0)
        pts_decepcion = detalles_forms.get("decepcion", 0)
        
        pts_extra_totales = float(jug['Puntos_Podio']) + float(jug['Puntos_Forms'])
        total = jug['TOTAL']

        # Ensamblar fila
        fila = [pos, nombre] + jornadas_columnas + [str(pts_sorpresa), str(pts_decepcion), f"{pts_extra_totales:.2f}", f"**{total}**"]
        md += "| " + " | ".join(fila) + " |\n"

    md += """
---
*🤖 Motor automatizado de puntuación.*
"""
    # Guardar en la raíz
    with open(ROOT_DIR / "README.md", 'w', encoding='utf-8') as f:
        f.write(md)
    print("✅ README.md global generado con éxito.")
    return True

def generar_readmes_personales():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]

    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        ruta_libro = jugador_dir / "estadisticas" / "historial_puntos.json"
        
        libro = cargar_json(ruta_libro)
        if not libro:
            continue

        posicion = libro.get("posicion_final_ranking", "-")
        total = libro.get("puntos_totales", 0)

        # Construir Markdown Personal (Estructura base, luego lo detallaremos si quieres)
        md = f"""# 👤 Perfil de Jugador: {nombre}
### Posición Actual: **{posicion}º** | Puntos Totales: **{total}**

---

## 📈 Resumen de Rendimiento
"""
        # Desglose de Jornadas
        md += "### 📅 Resumen de Jornadas\n"
        jornadas = libro.get("desglose_jornadas", {})
        if jornadas:
            for j, info in jornadas.items():
                if isinstance(info, dict):
                    icono = "🟡" if info["resultado"] == "Ganador" else ("🔴" if info["resultado"] == "Perdedor" else "⚪")
                    md += f"- **{j}:** {info['aciertos_1x2']} aciertos 1X2 | Bono: {info['puntos_bono']} pts {icono}\n"
        else:
            md += "*Aún no hay datos de jornadas.*\n"

        md += "\n---\n*Para consultar el desglose exacto partido a partido, abre tu archivo `estadisticas/historial_puntos.json`.*"
        md += "\n\n[⬅️ Volver a la clasificación general](../../README.md)"

        with open(jugador_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(md)
            
    print("✅ READMEs personales de todos los jugadores generados con éxito.")

def ejecutar_generador_vistas():
    print("=======================================================")
    print(" 🎨 INICIANDO GENERADOR DE VISTAS (MARKDOWN) 🎨")
    print("=======================================================")
    
    if generar_readme_global():
        generar_readmes_personales()
        print("\n🎉 ¡Tus vistas están listas! Sube los cambios a GitHub para ver la web.")

if __name__ == "__main__":
    ejecutar_generador_vistas()