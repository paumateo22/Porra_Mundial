import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from importlib import import_module

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

def cargar_configuracion():
    ruta = ROOT_DIR / "config" / "settings.json"
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

CONFIG = cargar_configuracion()

def calcular_clasificacion_grupos(fase_grupos):
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

            if p.get('estado', 'finished') == 'finished':
                if gl > gv: tabla[loc]["pts"] += 3
                elif gv > gl: tabla[vis]["pts"] += 3
                else:
                    tabla[loc]["pts"] += 1
                    tabla[vis]["pts"] += 1

        equipos_ordenados = sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"]), reverse=True)
        for idx, (eq, stats) in enumerate(equipos_ordenados): posiciones[eq] = idx + 1
    return posiciones

def obtener_racha_fases(jugador_dir, equipo, fase_objetivo):
    fases_cronologicas = ["grupos", "dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
    fase_busqueda_ocr = "finales" if fase_objetivo in ["final", "tercer_puesto", "finales"] else fase_objetivo
    fase_busqueda_infobae = "finales" if fase_objetivo in ["final", "tercer_puesto"] else fase_objetivo

    idx_limite = fases_cronologicas.index(fase_busqueda_ocr) if fase_busqueda_ocr in fases_cronologicas else 0
    rastros = []

    for i in range(idx_limite):
        fase_origen = fases_cronologicas[i]
        if fase_origen == "grupos":
            ruta_base = jugador_dir / "pronosticos" / "grupos" / f"{jugador_dir.name}_base.json"
            if ruta_base.exists():
                base = cargar_json(ruta_base)
                partidos_objetivo = base.get("eliminatorias", {}).get(fase_busqueda_infobae, [])
                for p in partidos_objetivo:
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        rastros.append(("Grupos", "pronosticos/grupos/"))
                        break
        else:
            ruta_ocr = jugador_dir / "pronosticos" / "eliminatorias" / fase_origen / f"{fase_origen}.json"
            if ruta_ocr.exists():
                ocr_data = cargar_json(ruta_ocr)
                partidos_objetivo = ocr_data.get("predicciones", {}).get(fase_busqueda_ocr, [])
                for p in partidos_objetivo:
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        nombres_cortos = {"dieciseisavos": "1/16", "octavos": "1/8", "cuartos": "1/4", "semifinales": "Semis"}
                        nombre_link = nombres_cortos.get(fase_origen, fase_origen)
                        rastros.append((nombre_link, f"pronosticos/eliminatorias/{fase_origen}/"))
                        break
    return rastros

def limpiar_nombre_archivo(nombre):
    """Elimina eñes, acentos y espacios para asegurar la persistencia en disco de las imágenes."""
    reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', ' ': '_'}
    res = nombre.lower()
    for orig, rep in reemplazos.items():
        res = res.replace(orig, rep)
    return "".join(c for c in res if c.isalnum() or c == '_') + "_sd.png"

# =====================================================================
# RENDERIZADOR DE IMÁGENES MATPLOTLIB (DASHBOARD SORPRESAS)
# =====================================================================
def generar_grafico_sd_png(ruta_salida, equipo, P, M, R):
    """Dibuja un gauge horizontal con las zonas válidas altamente visibles."""
    if not MATPLOTLIB_DISPONIBLE: return
    
    # Cast estricto para evitar que matplotlib use lógicas categóricas de strings
    P = int(P)
    M = float(M)
    R = int(R)
    
    fig, ax = plt.subplots(figsize=(6.5, 1.6), facecolor='white')
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.7, 0.7)

    ax.yaxis.set_visible(False)
    for spine in ax.spines.values(): spine.set_visible(False)

    fases = ["Grupos", "1/16", "1/8", "1/4", "Semis", "Final"]
    ax.set_xticks(range(6))
    ax.set_xticklabels(fases, fontsize=9, fontweight='bold', color='#374151')
    ax.tick_params(axis='x', length=0, pad=10)

    ax.axhline(0, color='#9ca3af', linewidth=4, zorder=1)

    if M - 1.5 >= -0.5:
        ax.axvspan(-0.5, M - 1.5, color='#fca5a5', alpha=0.35, zorder=0)
        ax.axvline(M - 1.5, color='#ef4444', linestyle='--', linewidth=2, zorder=2)
        ax.text((-0.5 + M - 1.5)/2, 0.45, "ZONA\nDECEPCIÓN", ha='center', va='center', 
                fontsize=7, color='#b91c1c', fontweight='black', 
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    if M + 1.5 <= 5.5:
        ax.axvspan(M + 1.5, 5.5, color='#86efac', alpha=0.35, zorder=0)
        ax.axvline(M + 1.5, color='#22c55e', linestyle='--', linewidth=2, zorder=2)
        ax.text((M + 1.5 + 5.5)/2, 0.45, "ZONA\nSORPRESA", ha='center', va='center', 
                fontsize=7, color='#15803d', fontweight='black', 
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    ax.plot(M, 0, 'o', color='#4b5563', markersize=14, zorder=3)
    ax.plot(P, 0, 's', color='#3b82f6', markersize=12, zorder=4)
    ax.plot(R, 0, '*', color='#eab308', markersize=22, markeredgecolor='black', markeredgewidth=0.5, zorder=5)

    y_media = 0.2
    y_tu = -0.25
    y_real = -0.5 if P == R else 0.35

    ax.text(M, y_media, "Media", ha='center', va='bottom', fontsize=8, color='#4b5563', fontweight='bold')
    ax.text(P, y_tu, "Tú", ha='center', va='top', fontsize=9, color='#1d4ed8', fontweight='bold')
    ax.text(R, y_real, "Realidad", ha='center', va='center', fontsize=9, color='#a16207', fontweight='bold')

    plt.tight_layout(pad=0.2)
    plt.savefig(ruta_salida, dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)

def generar_readme_global():
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    if not ruta_csv.exists(): return False

    jornadas_ruta = ROOT_DIR / "config" / "jornadas.json"
    jornadas_dict = cargar_json(jornadas_ruta) or {}
    jornadas_keys = list(jornadas_dict.keys())

    ranking = []
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader: ranking.append(row)

    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    headers = ["Pos", "Jugador"] + jornadas_keys + ["Pts Sorpresa", "Pts Decepción", "Premios", "TOTAL"]
    
    md = f"""# 🏆 Clasificación Oficial - Porra Mundial 2026 🏆\n\n*Última actualización: {fecha_act}*\n\nBienvenidos al panel oficial de la Porra. Aquí podéis consultar la clasificación general en tiempo real. \nEl formato de las jornadas es **Exactos/1x2**. Los colores indican: <span style="color:goldenrod">**Ganador**</span> de la jornada y <span style="color:red">**Perdedor**</span>.\n\n### 📊 Ranking General\n\n"""
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
                if desglose_p.get(clave, {}).get("acierto_exacto", False): exactos += 1
            
            aciertos_1x2 = info_j.get("aciertos_1x2", 0)
            texto_celda = f"{exactos}/{aciertos_1x2}"
            resultado = info_j.get("resultado", "")
            if resultado == "Ganador": texto_celda = f'<span style="color:goldenrod; font-weight:bold;">{texto_celda}</span>'
            elif resultado == "Perdedor": texto_celda = f'<span style="color:red; font-weight:bold;">{texto_celda}</span>'
            jornadas_columnas.append(texto_celda)

        premios = libro.get("premios_finales", {})
        detalles_forms = premios.get("formularios", {}).get("detalles", {})
        pts_extra_totales = float(jug['Puntos_Podio']) + float(jug['Puntos_Forms'])

        fila = [pos, nombre] + jornadas_columnas + [str(detalles_forms.get("sorpresa", 0)), str(detalles_forms.get("decepcion", 0)), f"{pts_extra_totales:.2f}", f"**{jug['TOTAL']}**"]
        md += "| " + " | ".join(fila) + " |\n"

    md += "\n---\n*🤖 Motor automatizado de puntuación.*\n"
    with open(ROOT_DIR / "README.md", 'w', encoding='utf-8') as f: f.write(md)
    return True

def generar_readmes_personales():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    jornadas_ruta = ROOT_DIR / "config" / "jornadas.json"
    jornadas_dict = cargar_json(jornadas_ruta) or {}
    jornadas_keys_list = list(jornadas_dict.keys())

    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    dict_reales = {}
    for grupo, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for fase, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

    jornada_global_hits = {}
    for j_dir in jugadores:
        libro_tmp = cargar_json(j_dir / "estadisticas" / "historial_puntos.json") or {}
        for jk, ji in libro_tmp.get("desglose_jornadas", {}).items():
            if jk not in jornada_global_hits: jornada_global_hits[jk] = {}
            jornada_global_hits[jk][j_dir.name] = ji.get("aciertos_1x2", 0)

    inc_racha = CONFIG["multiplicadores"]["incremento_racha_por_fase"]

    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        nombre_id = jugador_dir.name
        libro = cargar_json(jugador_dir / "estadisticas" / "historial_puntos.json")
        if not libro: continue

        dict_preds = {}
        ruta_base = jugador_dir / "pronosticos" / "grupos" / f"{nombre_id}_base.json"
        base_pred = cargar_json(ruta_base) or {}
        for grupo, partidos in base_pred.get("fase_grupos", {}).items():
            for p in partidos: dict_preds[f"{p['local']}_vs_{p['visitante']}"] = p

        for fase_origen in ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]:
            ruta_fase = jugador_dir / "pronosticos" / "eliminatorias" / fase_origen / f"{fase_origen}.json"
            datos = cargar_json(ruta_fase) or {}
            predicciones = datos.get("predicciones", {})
            for fase_destino, preds in predicciones.items():
                reales_fase = realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []) + realidad_dict.get("eliminatorias", {}).get("final", []) if fase_destino in ["finales", "final", "tercer_puesto"] else realidad_dict.get("eliminatorias", {}).get(fase_destino, [])
                for i, p_real in enumerate(reales_fase):
                    if i < len(preds): dict_preds[f"ID_{p_real['id_partido']}"] = preds[i]

        posicion = libro.get("posicion_final_ranking", "-")
        desglose_p = libro.get("desglose_partidos", {})
        desglose_j = libro.get("desglose_jornadas", {})

        md = f"# 👤 Perfil de Jugador: {nombre}\n### Posición Actual: **{posicion}º** | Puntos Totales: **{libro.get('puntos_totales', 0)}**\n---\n## 📅 Historial Cronológico de Partidos\nAquí tienes el detalle exacto de tus pronósticos y resultados oficiales.\n"
        pts_partidos_grupos_acumulados = 0
        pts_bonos_grupos_acumulados = 0
        pts_acumulados_historial = 0 

        for j_key in jornadas_keys_list:
            partidos_jornada = jornadas_dict[j_key]
            es_fase_grupos = j_key.startswith("J")
            fase_limpia = j_key.split(".")[0] if "." in j_key else j_key
            
            if j_key.lower() != "finales":
                md += f"### 📌 {j_key.upper()}\n"
                if es_fase_grupos:
                    md += "| Partido Oficial | Tu Pronóstico | Resultado Real | 1X2 | Exacto | Mult. | Pts |\n"
                    md += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n"
                else:
                    md += "| Partido Oficial | Tu Pronóstico | Resultado Real | 1X2 | Exacto | Mult. | Origen Extra | Pts |\n"
                    md += "| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |\n"
            
            pts_partidos_jornada = aciertos_jornada = exactos_jornada = 0
            partidos_jugados = False

            for idx_p, p in enumerate(partidos_jornada):
                
                if j_key.lower() == "finales":
                    if idx_p == 0:
                        md += f"### 🥉 TERCER PUESTO\n"
                        md += "| Partido Oficial | Tu Pronóstico | Resultado Real | 1X2 | Exacto | Mult. | Origen Extra | Pts |\n"
                        md += "| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |\n"
                    elif idx_p == 1:
                        md += f"\n### 🏆 FINAL\n"
                        md += "| Partido Oficial | Tu Pronóstico | Resultado Real | 1X2 | Exacto | Mult. | Origen Extra | Pts |\n"
                        md += "| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |\n"
                
                clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                info_p = desglose_p.get(clave, {})
                p_real = dict_reales.get(clave, {})
                p_pred = dict_preds.get(clave, {})
                
                loc_real = p_real.get("local", "TBD")
                vis_real = p_real.get("visitante", "TBD")
                
                if loc_real == "TBD" and "id_partido" in p: 
                    loc_real, vis_real = f"Eq. {p['id_partido']}A", f"Eq. {p['id_partido']}B"
                    
                if p_pred:
                    loc_pred, vis_pred = p_pred.get("local", ""), p_pred.get("visitante", "")
                    gl_pred, gv_pred = p_pred.get("goles_local", "-"), p_pred.get("goles_visitante", "-")
                    
                    if (loc_pred != p_real.get("local", "") or vis_pred != p_real.get("visitante", "")):
                        texto_pred = f"*{loc_pred} {gl_pred}-{gv_pred} {vis_pred}*" 
                    else: 
                        texto_pred = f"**{gl_pred} - {gv_pred}**"
                else: 
                    texto_pred = "-"

                estado = p_real.get("estado", "notstarted")
                if estado == "finished":
                    partidos_jugados = True
                    texto_real = f"**{p_real.get('goles_local', '-')} - {p_real.get('goles_visitante', '-')}**"
                    icono_1x2, icono_ex = ('✅' if info_p.get('acierto_1x2') else '❌'), ('🎯' if info_p.get('acierto_exacto') else '---')
                else:
                    texto_real = icono_1x2 = icono_ex = "⏳"

                pts = info_p.get("puntos_conseguidos", 0)
                mult = info_p.get('multiplicador_aplicado', 1.0)
                
                if estado == "finished" and info_p:
                    pts_partidos_jornada += pts
                    if info_p.get('acierto_1x2'): aciertos_jornada += 1
                    if info_p.get('acierto_exacto'): exactos_jornada += 1
                    if es_fase_grupos: pts_partidos_grupos_acumulados += pts
                
                if es_fase_grupos:
                    md += f"| **{loc_real}** vs **{vis_real}** | {texto_pred} | {texto_real} | {icono_1x2} | {icono_ex} | x{mult} | **{pts}** |\n"
                else:
                    texto_origen = "-"
                    if mult > 1.0 and estado == "finished":
                        eq_local_limpio = p_real.get("local")
                        eq_vis_limpio = p_real.get("visitante")
                        
                        rastros_loc = obtener_racha_fases(jugador_dir, eq_local_limpio, fase_limpia)
                        rastros_vis = obtener_racha_fases(jugador_dir, eq_vis_limpio, fase_limpia)
                        
                        detalles = []
                        if rastros_loc:
                            total_inc = len(rastros_loc) * inc_racha
                            links_loc = "; ".join([f"[{r[0]}]({r[1]})" for r in rastros_loc])
                            detalles.append(f"- **{eq_local_limpio}** +{total_inc}: {links_loc}")
                        if rastros_vis:
                            total_inc = len(rastros_vis) * inc_racha
                            links_vis = "; ".join([f"[{r[0]}]({r[1]})" for r in rastros_vis])
                            detalles.append(f"- **{eq_vis_limpio}** +{total_inc}: {links_vis}")
                        
                        if detalles: texto_origen = "<br>".join(detalles)
                    
                    md += f"| **{loc_real}** vs **{vis_real}** | {texto_pred} | {texto_real} | {icono_1x2} | {icono_ex} | x{mult} | {texto_origen} | **{pts}** |\n"
            
            info_jornada = desglose_j.get(j_key)
            bono_jornada = info_jornada.get("puntos_bono", 0) if info_jornada else 0
            pts_totales_jornada = pts_partidos_jornada + bono_jornada
            pts_acumulados_historial += pts_totales_jornada

            if info_jornada:
                if es_fase_grupos: pts_bonos_grupos_acumulados += bono_jornada
                resultado_str = info_jornada.get("resultado", "Neutral")
                icono_res = "🥇" if resultado_str == "Ganador" else ("🔴" if resultado_str == "Perdedor" else "⚪")

                hits_jugadores = jornada_global_hits.get(j_key, {})
                sorted_hits = sorted(hits_jugadores.items(), key=lambda x: x[1], reverse=True)
                rank = 1
                for idx, (pid, hits) in enumerate(sorted_hits):
                    if idx > 0 and hits < sorted_hits[idx-1][1]: rank = idx + 1
                    if pid == nombre_id: break
                md += f"\n> **Resumen de la {j_key.upper()}:** **{exactos_jornada}/{aciertos_jornada}** *(Clavados/Aciertos)*. Quedaste en la posición **{rank}º**. | Resultado: {icono_res} **{resultado_str}** ({bono_jornada} pts)\n> **Puntos sumados esta jornada:** {pts_totales_jornada} pts | **TOTAL ACUMULADO:** {pts_acumulados_historial} pts\n\n"
            else:
                if partidos_jugados: md += f"\n> **Resumen Parcial de la {j_key.upper()}:** **{exactos_jornada}/{aciertos_jornada}** *(Clavados/Aciertos)*.\n> **Puntos sumados hasta ahora:** {pts_totales_jornada} pts | **TOTAL ACUMULADO:** {pts_acumulados_historial} pts\n\n"
                else: md += "\n> *Jornada pendiente o sin procesar.*\n\n"

            if j_key == "J3.2":
                md += f"\n---\n## 📊 BALANCE DE FASE DE GRUPOS\n**Puntos obtenidos en partidos:** {pts_partidos_grupos_acumulados} pts\n**Puntos extra de jornadas:** {pts_bonos_grupos_acumulados} pts\n**TOTAL FASE DE GRUPOS (Sin contar bonos de pase): {pts_partidos_grupos_acumulados + pts_bonos_grupos_acumulados} pts**\n\n"
                md += "### Análisis de los 48 Equipos (Pase a Eliminatorias)\n| Equipo | Pasa (Tú) | Pos (Tú) | Pasa (Real) | Pos (Real) | Acierto Pase | Acierto Posición | Puntos |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
                
                pos_pred = calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
                pos_real = calcular_clasificacion_grupos(realidad_dict.get("fase_grupos", {}))
                pasan_pred = base_pred.get("clasificados_a_dieciseisavos", [])
                pasan_real = realidad_dict.get("clasificados_a_dieciseisavos", [])
                
                pts_por_grupos = libro.get("resolucion_fase_grupos", {}).get("puntos_conseguidos", 0)
                total_aciertos_pase = total_aciertos_exactos_pos = 0

                for eq in sorted(list(pos_real.keys())):
                    p_tu, pos_tu, p_rl, pos_rl = ("✅" if eq in pasan_pred else "❌"), f"{pos_pred.get(eq, '-')}º", ("✅" if eq in pasan_real else "❌"), f"{pos_real.get(eq, '-')}º"
                    if eq in pasan_real:
                        if eq in pasan_pred:
                            acierto_pase, pts_eq, total_aciertos_pase = "🎯 (+1)", 1, total_aciertos_pase + 1
                            if pos_pred.get(eq) == pos_real.get(eq): acierto_exacto, pts_eq, total_aciertos_exactos_pos = "🎯 (+2)", 3, total_aciertos_exactos_pos + 1
                            else: acierto_exacto = "❌"
                        else: acierto_pase = acierto_exacto = "❌"; pts_eq = 0
                    else: acierto_pase = acierto_exacto = "-"; pts_eq = 0
                    md += f"| **{eq}** | {p_tu} | {pos_tu} | {p_rl} | {pos_rl} | {acierto_pase} | {acierto_exacto} | **{pts_eq}** |\n"
                
                pts_acumulados_historial += pts_por_grupos
                md += f"\n> **Resumen de Clasificados:** **{total_aciertos_exactos_pos}/{total_aciertos_pase}** *(Clavados/Aciertos Pase)*\n> **Bono sumado por Fase de Grupos:** +{pts_por_grupos} pts | **TOTAL ACUMULADO:** {pts_acumulados_historial} pts\n\n---\n"

        # --- MATRIZ VISUAL DE SORPRESAS Y DECEPCIONES (CON GRÁFICOS) ---
        matriz_sd = libro.get("matriz_sorpresas_decepciones", {})
        if matriz_sd:
            dir_graficos = jugador_dir / "estadisticas" / "graficos_sd"
            dir_graficos.mkdir(parents=True, exist_ok=True)

            md += "\n## 🎯 Matriz de Desviaciones: Sorpresas y Decepciones\n"
            md += "Este gráfico analiza tu desviación respecto a la tendencia central de la comunidad. Las zonas coloreadas delimitan los rangos válidos para puntuar.\n\n"
            
            md += "| Selección | Datos | Gráfico de Rendimiento | Estado |\n"
            md += "| :--- | :---: | :---: | :---: |\n"

            for eq, datos_sd in sorted(matriz_sd.items()):
                P = datos_sd["pronostico"]
                M = datos_sd["media_grupo"]
                R = datos_sd["realidad"]
                puntos = datos_sd["puntos"]
                resultado_txt = datos_sd["resultado_calculo"]

                # Nombre de archivo sanitizado para evitar problemas de normalización de cadenas OS
                nombre_archivo = limpiar_nombre_archivo(eq)
                ruta_grafico = dir_graficos / nombre_archivo
                
                if MATPLOTLIB_DISPONIBLE:
                    generar_grafico_sd_png(ruta_grafico, eq, P, M, R)

                if resultado_txt == "Sorpresa": estado_str = f"🟢 **+{puntos} Pts**<br>🔥 ¡Sorpresa!"
                elif resultado_txt == "Decepción": estado_str = f"🔴 **+{puntos} Pts**<br>📉 ¡Decepción!"
                else: estado_str = f"⚪ *Sin Premio*<br>({puntos} pts)"

                valores_str = f"**Tú:** {P}<br>**Media:** {M}<br>**Real:** {R}"

                md += f"| **{eq}** | {valores_str} | ![{eq}](estadisticas/graficos_sd/{nombre_archivo}) | {estado_str} |\n"
            
            if not MATPLOTLIB_DISPONIBLE:
                md += "\n> ⚠️ *Nota: Instala matplotlib (`pip install matplotlib`) y vuelve a ejecutar para visualizar los gráficos.*\n"

            md += "\n> 💡 **Guía Visual del Eje:** `⚪` Media del grupo \\| `📌` Tu Pronóstico \\| `🎯` Resultado Real \\| `🟩` Umbral de Sorpresa Valido \\| `🟥` Umbral de Decepción Valido.\n"

        md += "\n---\n[⬅️ Volver a la clasificación general](../../README.md)"
        with open(jugador_dir / "README.md", 'w', encoding='utf-8') as f: f.write(md)

def ejecutar_generador_vistas():
    print("=======================================================")
    print(" 🎨 INICIANDO GENERADOR DE VISTAS (MARKDOWN) 🎨")
    print("=======================================================")
    if not MATPLOTLIB_DISPONIBLE:
        print("⚠️ AVISO: 'matplotlib' no está instalado. Los gráficos PNG no se generarán.")
        print("💡 Ejecuta: pip install matplotlib")

    if generar_readme_global():
        generar_readmes_personales()
        try:
            import_module("08_generador_realidad_md").generar_readme_realidad()
            import_module("09_generador_vistas_pronosticos").generar_readmes_pronosticos()
        except ModuleNotFoundError as e: pass
        print("\n🎉 ¡Tus vistas están listas! Sube los cambios a GitHub para ver la web.")

if __name__ == "__main__":
    ejecutar_generador_vistas()