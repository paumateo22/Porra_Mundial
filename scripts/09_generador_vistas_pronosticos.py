import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

# Versión limpia sin Markdown híbrido para tablas HTML
def formatear_resultado_html(p):
    gl, gv = str(p.get("goles_local", "-")), str(p.get("goles_visitante", "-"))
    if gl.isdigit() and gv.isdigit() and gl == gv:
        pl, pv = str(p.get("penaltis_local", "")), str(p.get("penaltis_visitante", ""))
        if pl.isdigit() and pv.isdigit(): return f"{gl} ({pl}) - ({pv}) {gv}"
    return f"{gl} - {gv}"

def formatear_resultado_md(p):
    gl, gv = str(p.get("goles_local", "-")), str(p.get("goles_visitante", "-"))
    if gl.isdigit() and gv.isdigit() and gl == gv:
        pl, pv = str(p.get("penaltis_local", "")), str(p.get("penaltis_visitante", ""))
        if pl.isdigit() and pv.isdigit(): return f"**{gl}** ({pl}) - ({pv}) **{gv}**"
    return f"**{gl}** - **{gv}**"

def calcular_clasificacion_grupo(partidos_grupo):
    tabla = {}
    for p in partidos_grupo:
        loc, vis = p.get('local', 'L'), p.get('visitante', 'V')
        if loc not in tabla: tabla[loc] = {"pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "dif": 0, "pts": 0}
        if vis not in tabla: tabla[vis] = {"pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "dif": 0, "pts": 0}

        gl_str, gv_str = str(p.get('goles_local', '')), str(p.get('goles_visitante', ''))
        if gl_str.isdigit() and gv_str.isdigit():
            gl, gv = int(gl_str), int(gv_str)
            tabla[loc]["pj"] += 1; tabla[vis]["pj"] += 1
            tabla[loc]["gf"] += gl; tabla[loc]["gc"] += gv
            tabla[vis]["gf"] += gv; tabla[vis]["gc"] += gl
            tabla[loc]["dif"] += (gl - gv); tabla[vis]["dif"] += (gv - gl)

            if gl > gv: tabla[loc]["pts"] += 3; tabla[loc]["pg"] += 1; tabla[vis]["pp"] += 1
            elif gv > gl: tabla[vis]["pts"] += 3; tabla[vis]["pg"] += 1; tabla[loc]["pp"] += 1
            else: tabla[loc]["pts"] += 1; tabla[vis]["pts"] += 1; tabla[loc]["pe"] += 1; tabla[vis]["pe"] += 1

    return sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"], x[1]["gf"]), reverse=True)

# =====================================================================
# EL CEREBRO DE VISUALIZACIÓN SIDE-BY-SIDE CON COLORES DINÁMICOS
# =====================================================================
def generar_html_eliminatorias(partidos_pred, reales_fase, sub_fase):
    html = "<table width='100%'>\n<tr><th width='50%' style='text-align:center;'>Tu Pronóstico</th><th width='50%' style='text-align:center;'>Resultado Real</th></tr>\n"
    
    for i, p_pred in enumerate(partidos_pred):
        # 1. Identificar Tercer Puesto/Final
        etiqueta = ""
        if sub_fase == "finales":
            if i == 0 and len(partidos_pred) > 1: etiqueta = "🥉 "
            elif i == len(partidos_pred) - 1: etiqueta = "🏆 "
        elif sub_fase == "tercer_puesto": etiqueta = "🥉 "
        elif sub_fase == "final": etiqueta = "🏆 "

        # 2. Formatear PRONÓSTICO (Lado izquierdo)
        loc_pred = f"{etiqueta}{p_pred.get('local', '-')}"
        vis_pred = p_pred.get("visitante", "-")
        res_pred_raw = formatear_resultado_html(p_pred)
        avanza_pred = p_pred.get("pasa", p_pred.get("ganador", "-"))

        # 3. Formatear REALIDAD (Lado derecho) y Lógica de Colores
        p_real = reales_fase[i] if i < len(reales_fase) else {}
        
        color_fondo = "white" # Default neutral
        icon_outcome = "⚪ Neutral"
        
        if p_real and p_real.get("estado") == "finished":
            # Realidad
            loc_real = f"{etiqueta}{p_real.get('local', '-')}"
            vis_real = p_real.get("visitante", "-")
            res_real = formatear_resultado_html(p_real)
            
            # Quién avanza en realidad
            gl, gv = int(p_real.get("goles_local", 0)), int(p_real.get("goles_visitante", 0))
            if gl > gv: avanza_real = p_real.get("local", "-")
            elif gv > gl: avanza_real = p_real.get("visitante", "-")
            else:
                pl, pv = int(p_real.get("penaltis_local", 0)), int(p_real.get("penaltis_visitante", 0))
                avanza_real = p_real.get("local", "-") if pl > pv else p_real.get("visitante", "-")

            # --- LA JERGA DE COLORES ---
            # Outcome (1X2)
            sig_p = "1" if int(p_pred.get("goles_local",0)) > int(p_pred.get("goles_visitante",0)) else ("2" if int(p_pred.get("goles_visitante",0)) > int(p_pred.get("goles_local",0)) else "X")
            sig_r = "1" if gl > gv else ("2" if gv > gl else "X")
            
            # Exacto
            ex_p = f"{p_pred.get('goles_local')}-{p_pred.get('goles_visitante')}"
            ex_r = f"{gl}-{gv}"

            if sig_p != sig_r:
                color_fondo = "#fee2e2" # Rojo suave (fallado)
                icon_outcome = "🔴 Fallado"
            else:
                if ex_p != ex_r:
                    color_fondo = "#fef9c3" # Amarillo suave (acierto 1X2)
                    icon_outcome = "🟨 Acertado"
                else:
                    color_fondo = "#dcfce7" # Verde suave (clavado)
                    icon_outcome = "🟢 Clavado"
        else:
            # Pendiente
            loc_real_name = p_real.get("local", "TBD") if "local" in p_real else f"Eq. {p_real.get('id_partido','')}A"
            vis_real_name = p_real.get("visitante", "TBD") if "visitante" in p_real else f"Eq. {p_real.get('id_partido','')}B"
            loc_real, vis_real = f"{etiqueta}{loc_real_name}", vis_real_name
            res_real = "⏳ Pendiente"
            avanza_real = "-"

        # 4. Generar Fila HTML Limpia
        html += f"<tr>"
        html += f"<td align='center' style='background-color:{color_fondo}; border:1px solid #e5e7eb; padding:10px;'>"
        html += f"<b>{loc_pred}</b> <b style='font-size:1.1em;'>{res_pred_raw}</b> <b>{vis_pred}</b><br>"
        html += f"<span style='color:#6b7280; font-size:0.9em;'>🟢 Avanza: {avanza_pred}</span><br>"
        html += f"<span style='font-weight:bold; font-size:0.9em;'>{icon_outcome}</span>"
        html += f"</td>"
        
        html += f"<td align='center' style='border:1px solid #e5e7eb; padding:10px;'>"
        html += f"<b>{loc_real}</b> <b style='font-size:1.1em;'>{res_real}</b> <b>{vis_real}</b><br>"
        html += f"<span style='color:#6b7280; font-size:0.9em;'>🟢 Avanza: {avanza_real}</span>"
        html += f"</td>"
        html += f"</tr>\n"
        
    html += "</table>\n"
    return html

def obtener_reales_fase(realidad_dict, sub_fase):
    if sub_fase in ["finales", "final", "tercer_puesto"]:
        reales = []
        reales.extend(realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []))
        reales.extend(realidad_dict.get("eliminatorias", {}).get("final", []))
        return reales
    return realidad_dict.get("eliminatorias", {}).get(sub_fase, [])

def generar_readme_grupos(jugador_dir, nombre, dict_reales, realidad_dict):
    nombre_id = jugador_dir.name
    ruta_json = jugador_dir / "pronosticos" / "grupos" / f"{nombre_id}_base.json"
    if not ruta_json.exists(): return

    datos = cargar_json(ruta_json)
    if not datos: return

    clasificados = datos.get("clasificados_a_dieciseisavos", [])
    fase_grupos = datos.get("fase_grupos", {})

    md = f"# 🌍 Pronóstico Inicial Completo - {nombre}\n\nAquí puedes consultar las tablas y el camino exacto hacia la final que predijo el jugador antes de empezar el torneo.\n\n---\n\n"

    # 1. TABLAS DE GRUPOS ORDENADAS ALFABÉTICAMENTE (A -> L)
    for grupo, partidos in sorted(fase_grupos.items(), key=lambda x: x[0]):
        nombre_grupo = grupo.replace('_', ' ').upper()
        md += f"## 📊 {nombre_grupo}\n"
        md += "| Pos | Equipo | PJ | PG | PE | PP | GF | GC | DIF | PTS | Pase |\n"
        md += "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        
        posiciones = calcular_clasificacion_grupo(partidos)
        for idx, (eq, stats) in enumerate(posiciones):
            pos_str, pasa = f"**{idx + 1}º**", ("✅" if eq in clasificados else "❌")
            md += f"| {pos_str} | **{eq}** | {stats['pj']} | {stats['pg']} | {stats['pe']} | {stats['pp']} | {stats['gf']} | {stats['gc']} | {stats['dif']} | **{stats['pts']}** | {pasa} |\n"
        
        # TABLA LADO A LADO HTML PARA GRUPOS (Tu Pronóstico vs Real)
        md += "\n<details><summary><b>Ver Partidos del Grupo (Tu Pronóstico vs Real)</b></summary><br>\n\n"
        html_grupos = "<table width='100%'>\n<tr><th width='50%' style='text-align:center;'>Tu Pronóstico</th><th width='50%' style='text-align:center;'>Resultado Real</th></tr>\n"
        
        for p in partidos:
            loc, vis = p.get('local', '-'), p.get('visitante', '-')
            # Usamos formato limpio sin asteriscos híbridos
            res_pred_raw = formatear_resultado_html(p)
            
            p_real = dict_reales.get(f"{loc}_vs_{vis}", {})
            if not p_real: p_real = dict_reales.get(f"{vis}_vs_{loc}", {}) # Por SofaScore

            color_fondo = "white"
            icon_outcome = "⚪Neutral"

            if p_real and p_real.get("estado") == "finished":
                loc_real, vis_real = p_real.get("local", "-"), p_real.get("visitante", "-")
                res_real_raw = formatear_resultado_html(p_real)
                
                # Jerga Colores
                gl_r, gv_r = int(p_real.get("goles_local",0)), int(p_real.get("goles_visitante",0))
                sig_p = "1" if int(p.get("goles_local",0)) > int(p.get("goles_visitante",0)) else ("2" if int(p.get("goles_visitante",0)) > int(p.get("goles_local",0)) else "X")
                sig_r = "1" if gl_r > gv_r else ("2" if gv_r > gl_r else "X")
                ex_p = f"{p.get('goles_local')}-{p.get('goles_visitante')}"
                ex_r = f"{gl_r}-{gv_r}"

                if sig_p != sig_r:
                    color_fondo = "#fee2e2"; icon_outcome = "🔴 Fallado"
                else:
                    if ex_p != ex_r:
                        color_fondo = "#fef9c3"; icon_outcome = "🟨 Acertado"
                    else:
                        color_fondo = "#dcfce7"; icon_outcome = "🟢 Clavado"
            else:
                loc_real, vis_real, res_real_raw = loc, vis, "⏳ Pendiente"
                
            html_grupos += f"<tr>"
            html_grupos += f"<td align='center' style='background-color:{color_fondo}; border:1px solid #e5e7eb; padding:10px;'>"
            html_grupos += f"<b>{loc}</b> <b style='font-size:1.1em;'>{res_pred_raw}</b> <b>{vis}</b><br><span style='font-weight:bold; font-size:0.9em;'>{icon_outcome}</span>"
            html_grupos += f"</td>"
            html_grupos += f"<td align='center' style='border:1px solid #e5e7eb; padding:10px;'><b>{loc_real}</b> <b style='font-size:1.1em;'>{res_real_raw}</b> <b>{vis_real}</b></td>"
            html_grupos += f"</tr>\n"
            
        html_grupos += "</table>\n</details>\n\n---\n"
        md += html_grupos

    # 2. EL ÁRBOL COMPLETO HASTA LA FINAL (Si está en el base.json) SIDE-BY-SIDE
    eliminatorias = datos.get("eliminatorias", {})
    if eliminatorias:
        md += "\n## ⚔️ Camino a la Final (Pronóstico Original vs Realidad)\n\n"
        orden_logico = ["dieciseisavos", "octavos", "cuartos", "semifinales", "tercer_puesto", "final", "finales"]
        
        for sub_fase in orden_logico:
            partidos_sub = eliminatorias.get(sub_fase, [])
            if partidos_sub:
                md += f"### 🏆 {sub_fase.replace('_', ' ').upper()}\n"
                reales_fase = obtener_reales_fase(realidad_dict, sub_fase)
                md += generar_html_eliminatorias(partidos_sub, reales_fase, sub_fase)
                md += "\n"

    with open(jugador_dir / "pronosticos" / "grupos" / "README.md", 'w', encoding='utf-8') as f: f.write(md)

def generar_readme_eliminatorias(jugador_dir, nombre, realidad_dict):
    fases = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
    for fase in fases:
        ruta_carpeta = jugador_dir / "pronosticos" / "eliminatorias" / fase
        ruta_json = ruta_carpeta / f"{fase}.json"
        
        if not ruta_json.exists(): continue
        
        datos = cargar_json(ruta_json)
        predicciones = datos.get("predicciones", {}) if datos else {}
        if not predicciones: continue

        md = f"# ⚔️ Cuadro Predictivo desde {fase.capitalize()} - {nombre}\n\nEsta es la hoja de ruta que imaginó el jugador cuando arrancaron los {fase.capitalize()}.\n\n---\n\n"
        orden_logico = ["dieciseisavos", "octavos", "cuartos", "semifinales", "tercer_puesto", "final", "finales"]
        
        for sub_fase in orden_logico:
            if sub_fase in predicciones:
                partidos = predicciones[sub_fase]
                md += f"### 🏆 {sub_fase.replace('_', ' ').upper()}\n"
                reales_fase = obtener_reales_fase(realidad_dict, sub_fase)
                # Tablas Lado a Lado con Colores
                md += generar_html_eliminatorias(partidos, reales_fase, sub_fase)
                md += "\n"

        with open(ruta_carpeta / "README.md", 'w', encoding='utf-8') as f: f.write(md)

def generar_readmes_pronosticos():
    print("=======================================================")
    print(" 🎨 [09] GENERANDO MUSEOS DE PRONÓSTICOS (CARPETAS LOCALES) ")
    print("=======================================================")
    
    dir_participantes = ROOT_DIR / "participantes"
    if not dir_participantes.exists(): return
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    dict_reales = {}
    for grupo, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    
    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        generar_readme_grupos(jugador_dir, nombre, dict_reales, realidad_dict)
        generar_readme_eliminatorias(jugador_dir, nombre, realidad_dict)
        
    print("✅ Vistas de pronósticos internos generadas con éxito.")

if __name__ == "__main__":
    generar_readmes_pronosticos()