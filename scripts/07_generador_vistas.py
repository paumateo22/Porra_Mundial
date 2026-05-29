import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from importlib import import_module

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
    headers = ["Pos", "Jugador"] + jornadas_keys + ["Pts Sorpresa", "Pts Decepción", "Premios", "TOTAL"]
    
    md = f"""# 🏆 Clasificación Oficial - Porra Mundial 2026 🏆
    
*Última actualización: {fecha_act}*

Bienvenidos al panel oficial de la Porra. Aquí podéis consultar la clasificación general en tiempo real. 
El formato de las jornadas es **Exactos/1x2**. Los colores indican: <span style="color:goldenrod">**Ganador**</span> de la jornada y <span style="color:red">**Perdedor**</span>.

### 📊 Ranking General

"""
    md += "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join([":---:" if h != "Jugador" else ":---" for h in headers]) + " |\n"

    for jug in ranking:
        nombre_id = jug['Jugador'].replace(' ', '_').lower()
        ruta_libro = ROOT_DIR / "participantes" / nombre_id / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro) or {}
        
        pos = jug['Posicion']
        if pos == "1": pos = "🥇 1º"
        elif pos == "2": pos = "🥈 2º"
        elif pos == "3": pos = "🥉 3º"
        else: pos = f"{pos}º"

        nombre = f"**[{jug['Jugador']}](participantes/{nombre_id}/README.md)**"
        
        jornadas_columnas = []
        desglose_j = libro.get("desglose_jornadas", {})
        desglose_p = libro.get("desglose_partidos", {})
        
        for j_key in jornadas_keys:
            info_j = desglose_j.get(j_key)
            if not info_j:
                jornadas_columnas.append("-")
                continue
                
            exactos = 0
            partidos_de_esta_jornada = jornadas_dict.get(j_key, [])
            for p in partidos_de_esta_jornada:
                clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                if desglose_p.get(clave, {}).get("acierto_exacto", False):
                    exactos += 1
            
            aciertos_1x2 = info_j.get("aciertos_1x2", 0)
            texto_celda = f"{exactos}/{aciertos_1x2}"
            resultado = info_j.get("resultado", "")
            
            if resultado == "Ganador":
                texto_celda = f'<span style="color:goldenrod; font-weight:bold;">{texto_celda}</span>'
            elif resultado == "Perdedor":
                texto_celda = f'<span style="color:red; font-weight:bold;">{texto_celda}</span>'
                
            jornadas_columnas.append(texto_celda)

        premios = libro.get("premios_finales", {})
        forms = premios.get("formularios", {})
        detalles_forms = forms.get("detalles", {})
        
        pts_sorpresa = detalles_forms.get("sorpresa", 0)
        pts_decepcion = detalles_forms.get("decepcion", 0)
        
        pts_extra_totales = float(jug['Puntos_Podio']) + float(jug['Puntos_Forms'])
        total = jug['TOTAL']

        fila = [pos, nombre] + jornadas_columnas + [str(pts_sorpresa), str(pts_decepcion), f"{pts_extra_totales:.2f}", f"**{total}**"]
        md += "| " + " | ".join(fila) + " |\n"

    md += """
---
*🤖 Motor automatizado de puntuación.*
"""
    with open(ROOT_DIR / "README.md", 'w', encoding='utf-8') as f:
        f.write(md)
    print("✅ README.md global generado con éxito.")
    return True

def generar_readmes_personales():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    jornadas_ruta = ROOT_DIR / "config" / "jornadas.json"
    jornadas_dict = cargar_json(jornadas_ruta) or {}

    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    realidad_dict = cargar_json(ruta_realidad) or {}

    # 1. Mapa global de la realidad para acceso directo
    dict_reales = {}
    for grupo, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos:
            dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for fase, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p:
                dict_reales[f"ID_{p['id_partido']}"] = p

    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        nombre_id = jugador_dir.name
        ruta_libro = jugador_dir / "estadisticas" / "historial_puntos.json"
        
        libro = cargar_json(ruta_libro)
        if not libro:
            continue

        # 2. Mapa de predicciones del jugador
        dict_preds = {}
        
        # 2.1 Extraer predicciones de grupos
        ruta_base = jugador_dir / "pronosticos" / "grupos" / f"{nombre_id}_base.json"
        base_pred = cargar_json(ruta_base) or {}
        for grupo, partidos in base_pred.get("fase_grupos", {}).items():
            for p in partidos:
                dict_preds[f"{p['local']}_vs_{p['visitante']}"] = p

        # 2.2 Extraer predicciones de eliminatorias (Mapeadas por ID real)
        fases_ocr = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
        for fase in fases_ocr:
            ruta_fase = jugador_dir / "pronosticos" / "eliminatorias" / fase / f"{fase}.json"
            pred_fase = cargar_json(ruta_fase) or {}
            preds = pred_fase.get("predicciones", {}).get(fase, [])
            
            reales_fase = []
            if fase == "finales":
                reales_fase.extend(realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []))
                reales_fase.extend(realidad_dict.get("eliminatorias", {}).get("final", []))
            else:
                reales_fase = realidad_dict.get("eliminatorias", {}).get(fase, [])

            for i, p_real in enumerate(reales_fase):
                if i < len(preds):
                    dict_preds[f"ID_{p_real['id_partido']}"] = preds[i]

        posicion = libro.get("posicion_final_ranking", "-")
        total = libro.get("puntos_totales", 0)
        desglose_p = libro.get("desglose_partidos", {})

        md = f"""# 👤 Perfil de Jugador: {nombre}
### Posición Actual: **{posicion}º** | Puntos Totales: **{total}**

---

## 📅 Historial Cronológico de Partidos

Aquí tienes el detalle exacto de tus pronósticos y resultados oficiales.

"""
        for j_key, partidos_jornada in jornadas_dict.items():
            md += f"### 📌 {j_key.upper()}\n"
            md += "| Partido Oficial | Tu Pronóstico | Resultado Real | 1X2 | Exacto | Mult. | Pts |\n"
            md += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n"
            
            partidos_encontrados = False
            for p in partidos_jornada:
                clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                
                info_partido = desglose_p.get(clave)
                if info_partido:
                    partidos_encontrados = True
                    p_real = dict_reales.get(clave, {})
                    p_pred = dict_preds.get(clave, {})
                    
                    loc_real = p_real.get("local", "L")
                    vis_real = p_real.get("visitante", "V")
                    nombre_mostrar = f"**{loc_real}** vs **{vis_real}**"

                    # Gestión de la columna "Tu Pronóstico"
                    if p_pred:
                        loc_pred = p_pred.get("local", "")
                        vis_pred = p_pred.get("visitante", "")
                        gl_pred = p_pred.get("goles_local", "-")
                        gv_pred = p_pred.get("goles_visitante", "-")
                        
                        # Si el jugador predijo otros equipos para ese cruce
                        if loc_pred != loc_real or vis_pred != vis_real:
                            texto_pred = f"*{loc_pred} {gl_pred}-{gv_pred} {vis_pred}*"
                        else:
                            texto_pred = f"**{gl_pred} - {gv_pred}**"
                    else:
                        texto_pred = "-"

                    # Gestión de la columna "Resultado Real"
                    if p_real.get("estado") == "finished":
                        gl_real = p_real.get("goles_local", "-")
                        gv_real = p_real.get("goles_visitante", "-")
                        texto_real = f"**{gl_real} - {gv_real}**"
                    else:
                        texto_real = "⏳"
                    
                    icono_1x2 = "✅" if info_partido.get("acierto_1x2") else "❌"
                    icono_ex = "🎯" if info_partido.get("acierto_exacto") else "---"
                    pts = info_partido.get("puntos_conseguidos", 0)
                    
                    # El multiplicador ahora siempre muestra su valor
                    mult = info_partido.get("multiplicador_aplicado", 1.0)
                    str_mult = f"x{mult}"
                    
                    md += f"| {nombre_mostrar} | {texto_pred} | {texto_real} | {icono_1x2} | {icono_ex} | {str_mult} | **{pts}** |\n"
            
            if not partidos_encontrados:
                md += "| *Aún no hay resultados para esta jornada.* | - | - | - | - | - | - |\n"
            
            md += "\n"

        md += "\n---\n[⬅️ Volver a la clasificación general](../../README.md)"

        with open(jugador_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(md)
            
    print("✅ READMEs personales generados con las columnas de Pronóstico y Realidad.")

def ejecutar_generador_vistas():
    print("=======================================================")
    print(" 🎨 INICIANDO GENERADOR DE VISTAS (MARKDOWN) 🎨")
    print("=======================================================")
    
    if generar_readme_global():
        generar_readmes_personales()
        
        print("\n📝 Generando periódico de resultados reales...")
        try:
            import_module("08_generador_realidad_md").generar_readme_realidad()
        except ModuleNotFoundError:
            print("⚠️ No se encontró el script 08_generador_realidad_md.py")
            
        print("\n🎉 ¡Tus vistas están listas! Sube los cambios a GitHub para ver la web.")

if __name__ == "__main__":
    ejecutar_generador_vistas()