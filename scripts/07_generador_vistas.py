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

def calcular_clasificacion_grupos(fase_grupos):
    """Calcula la posición (1º, 2º, 3º, 4º) de cada equipo en su grupo."""
    posiciones = {}
    for grupo, partidos in fase_grupos.items():
        tabla = {}
        for p in partidos:
            loc, vis = p['local'], p['visitante']
            if loc not in tabla: tabla[loc] = {"pts": 0, "dif": 0}
            if vis not in tabla: tabla[vis] = {"pts": 0, "dif": 0}

            gl = int(p.get('goles_local', 0)) if str(p.get('goles_local', '')).isdigit() else 0
            gv = int(p.get('goles_visitante', 0)) if str(p.get('goles_visitante', '')).isdigit() else 0

            tabla[loc]["dif"] += (gl - gv)
            tabla[vis]["dif"] += (gv - gl)

            # En predicciones contamos siempre. En la realidad oficial, solo si ha terminado.
            if p.get('estado', 'finished') == 'finished':
                if gl > gv: tabla[loc]["pts"] += 3
                elif gv > gl: tabla[vis]["pts"] += 3
                else:
                    tabla[loc]["pts"] += 1
                    tabla[vis]["pts"] += 1

        # Ordenamos primero por puntos y luego por diferencia de goles
        equipos_ordenados = sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"]), reverse=True)
        for idx, (eq, stats) in enumerate(equipos_ordenados):
            posiciones[eq] = idx + 1
    return posiciones

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
            for p in jornadas_dict.get(j_key, []):
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
        detalles_forms = premios.get("formularios", {}).get("detalles", {})
        pts_extra_totales = float(jug['Puntos_Podio']) + float(jug['Puntos_Forms'])

        fila = [pos, nombre] + jornadas_columnas + [str(detalles_forms.get("sorpresa", 0)), str(detalles_forms.get("decepcion", 0)), f"{pts_extra_totales:.2f}", f"**{jug['TOTAL']}**"]
        md += "| " + " | ".join(fila) + " |\n"

    md += "\n---\n*🤖 Motor automatizado de puntuación.*\n"
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

    # 1. Mapa de Realidad
    dict_reales = {}
    for grupo, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for fase, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

    # 2. Pre-cálculo global para sacar Rankings de Jornadas
    jornada_global_hits = {}
    for j_dir in jugadores:
        libro_tmp = cargar_json(j_dir / "estadisticas" / "historial_puntos.json") or {}
        for jk, ji in libro_tmp.get("desglose_jornadas", {}).items():
            if jk not in jornada_global_hits: jornada_global_hits[jk] = {}
            jornada_global_hits[jk][j_dir.name] = ji.get("aciertos_1x2", 0)

    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        nombre_id = jugador_dir.name
        libro = cargar_json(jugador_dir / "estadisticas" / "historial_puntos.json")
        if not libro: continue

        # 3. Predicciones Base
        ruta_base = jugador_dir / "pronosticos" / "grupos" / f"{nombre_id}_base.json"
        base_pred = cargar_json(ruta_base) or {}
        dict_preds = {}
        for grupo, partidos in base_pred.get("fase_grupos", {}).items():
            for p in partidos: dict_preds[f"{p['local']}_vs_{p['visitante']}"] = p

        for fase in ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]:
            ruta_fase = jugador_dir / "pronosticos" / "eliminatorias" / fase / f"{fase}.json"
            preds = (cargar_json(ruta_fase) or {}).get("predicciones", {}).get(fase, [])
            reales_fase = realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []) + realidad_dict.get("eliminatorias", {}).get("final", []) if fase == "finales" else realidad_dict.get("eliminatorias", {}).get(fase, [])
            for i, p_real in enumerate(reales_fase):
                if i < len(preds): dict_preds[f"ID_{p_real['id_partido']}"] = preds[i]

        posicion = libro.get("posicion_final_ranking", "-")
        desglose_p = libro.get("desglose_partidos", {})
        desglose_j = libro.get("desglose_jornadas", {})

        md = f"""# 👤 Perfil de Jugador: {nombre}
### Posición Actual: **{posicion}º** | Puntos Totales: **{libro.get("puntos_totales", 0)}**

---

## 📅 Historial Cronológico de Partidos

Aquí tienes el detalle exacto de tus pronósticos y resultados oficiales.
"""
        pts_partidos_grupos_acumulados = 0
        pts_bonos_grupos_acumulados = 0

        for j_key, partidos_jornada in jornadas_dict.items():
            es_fase_grupos = j_key.startswith("J")
            
            md += f"### 📌 {j_key.upper()}\n"
            md += "| Partido Oficial | Tu Pronóstico | Resultado Real | 1X2 | Exacto | Mult. | Pts |\n"
            md += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n"
            
            for p in partidos_jornada:
                clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                info_p = desglose_p.get(clave)
                if info_p:
                    p_real = dict_reales.get(clave, {})
                    p_pred = dict_preds.get(clave, {})
                    
                    loc_real, vis_real = p_real.get("local", "L"), p_real.get("visitante", "V")
                    
                    if p_pred:
                        loc_pred, vis_pred = p_pred.get("local", ""), p_pred.get("visitante", "")
                        gl_pred, gv_pred = p_pred.get("goles_local", "-"), p_pred.get("goles_visitante", "-")
                        texto_pred = f"*{loc_pred} {gl_pred}-{gv_pred} {vis_pred}*" if (loc_pred != loc_real or vis_pred != vis_real) else f"**{gl_pred} - {gv_pred}**"
                    else:
                        texto_pred = "-"

                    texto_real = f"**{p_real.get('goles_local', '-')} - {p_real.get('goles_visitante', '-')}**" if p_real.get("estado") == "finished" else "⏳"
                    pts = info_p.get("puntos_conseguidos", 0)
                    
                    if es_fase_grupos: pts_partidos_grupos_acumulados += pts
                    
                    md += f"| **{loc_real}** vs **{vis_real}** | {texto_pred} | {texto_real} | {'✅' if info_p.get('acierto_1x2') else '❌'} | {'🎯' if info_p.get('acierto_exacto') else '---'} | x{info_p.get('multiplicador_aplicado', 1.0)} | **{pts}** |\n"
            
            # BLOQUE RESUMEN DE JORNADA
            info_jornada = desglose_j.get(j_key)
            if info_jornada:
                aciertos = info_jornada.get("aciertos_1x2", 0)
                bono = info_jornada.get("puntos_bono", 0)
                resultado_str = info_jornada.get("resultado", "Neutral")
                
                if es_fase_grupos: pts_bonos_grupos_acumulados += bono

                # Calcular la posición en esta jornada
                hits_jugadores = jornada_global_hits.get(j_key, {})
                sorted_hits = sorted(hits_jugadores.items(), key=lambda x: x[1], reverse=True)
                rank = 1
                for idx, (pid, hits) in enumerate(sorted_hits):
                    if idx > 0 and hits < sorted_hits[idx-1][1]: rank = idx + 1
                    if pid == nombre_id: break
                
                icono_res = "🥇" if resultado_str == "Ganador" else ("🔴" if resultado_str == "Perdedor" else "⚪")
                md += f"\n> **Resumen de la {j_key.upper()}:** Has logrado **{aciertos}** aciertos (1X2). Quedaste en la posición **{rank}º**. | Resultado: {icono_res} **{resultado_str}** ({bono} pts)\n\n"
            else:
                md += "\n> *Jornada pendiente o sin procesar.*\n\n"

            # --- CORTE: RECUENTO DE FASE DE GRUPOS ---
            if j_key == "J3.2":
                md += "\n---\n## 📊 BALANCE DE FASE DE GRUPOS\n"
                md += f"**Puntos obtenidos en partidos:** {pts_partidos_grupos_acumulados} pts\n"
                md += f"**Puntos extra de jornadas:** {pts_bonos_grupos_acumulados} pts\n"
                md += f"**TOTAL FASE DE GRUPOS (Sin contar bonos de pase): {pts_partidos_grupos_acumulados + pts_bonos_grupos_acumulados} pts**\n\n"
                
                # --- TABLA 48 EQUIPOS ---
                md += "### Análisis de los 48 Equipos (Pase a Eliminatorias)\n"
                md += "| Equipo | Pasa (Tú) | Pos (Tú) | Pasa (Real) | Pos (Real) | Acierto Pase | Acierto Exacto |\n"
                md += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n"
                
                pos_pred = calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
                pos_real = calcular_clasificacion_grupos(realidad_dict.get("fase_grupos", {}))
                pasan_pred = base_pred.get("clasificados_a_dieciseisavos", [])
                pasan_real = realidad_dict.get("clasificados_a_dieciseisavos", [])
                
                # Para mostrar puntos sumados por acierto de grupos (si procede)
                pts_por_grupos = libro.get("resolucion_fase_grupos", {}).get("puntos_conseguidos", 0)
                
                for eq in sorted(list(pos_real.keys())):
                    p_tu = "✅" if eq in pasan_pred else "❌"
                    pos_tu = f"{pos_pred.get(eq, '-')}º"
                    p_rl = "✅" if eq in pasan_real else "❌"
                    pos_rl = f"{pos_real.get(eq, '-')}º"
                    
                    acierto_pase = "🎯" if (eq in pasan_pred) == (eq in pasan_real) else "---"
                    acierto_exacto = "🎯" if pos_pred.get(eq) == pos_real.get(eq) else "---"
                    
                    md += f"| **{eq}** | {p_tu} | {pos_tu} | {p_rl} | {pos_rl} | {acierto_pase} | {acierto_exacto} |\n"
                
                md += f"\n**Bono total por aciertos en Fase de Grupos:** +{pts_por_grupos} pts\n\n---\n"

        md += "\n---\n[⬅️ Volver a la clasificación general](../../README.md)"

        with open(jugador_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(md)
            
    print("✅ READMEs personales generados con recuentos de Jornada y Tabla de 48 equipos.")

def ejecutar_generador_vistas():
    print("=======================================================")
    print(" 🎨 INICIANDO GENERADOR DE VISTAS (MARKDOWN) 🎨")
    print("=======================================================")
    
    if generar_readme_global():
        generar_readmes_personales()
        try:
            import_module("08_generador_realidad_md").generar_readme_realidad()
        except ModuleNotFoundError:
            pass
        print("\n🎉 ¡Tus vistas están listas! Sube los cambios a GitHub para ver la web.")

if __name__ == "__main__":
    ejecutar_generador_vistas()