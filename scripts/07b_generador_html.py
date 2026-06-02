import sys
import json
import csv
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

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

def limpiar_nombre_archivo(nombre):
    reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', ' ': '_'}
    res = nombre.lower()
    for orig, rep in reemplazos.items(): res = res.replace(orig, rep)
    return "".join(c for c in res if c.isalnum() or c == '_') + "_sd.png"

def get_sidebar_html(depth=""):
    return f"""
    <div id="mySidenav" class="sidenav">
        <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
        <a href="{depth}index.html">🏠 Clasificación Global</a>
        <a href="{depth}calendario.html">📅 Calendario Oficial</a>
        <a href="{depth}participantes.html">👥 Participantes</a>
        <a href="#" style="color:gray;">📈 Análisis de Datos (Pronto)</a>
    </div>
    <div class="menu-btn" onclick="openNav()">&#9776;</div>
    <script>
        function openNav() {{ document.getElementById("mySidenav").style.width = "250px"; }}
        function closeNav() {{ document.getElementById("mySidenav").style.width = "0"; }}
    </script>
    """

# =====================================================================
# PÁGINA 1: INDEX (RANKING)
# =====================================================================
def generar_index_html():
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    if not ruta_csv.exists(): return False

    jornadas_dict = cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    
    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    pos_real = calcular_clasificacion_grupos(realidad_dict.get("fase_grupos", {}))
    pasan_real = realidad_dict.get("clasificados_a_dieciseisavos", [])

    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏆 Porra Mundial 2026</title>
    <link rel="stylesheet" href="theme.css">
</head>
<body>
    {get_sidebar_html("")}
    <header>
        <h1>🏆 Porra Mundial 2026</h1>
        <p>Panel de Estadísticas Oficiales | Actualizado: {fecha_act}</p>
    </header>
    <div class="container">
"""
    jugadores_datos = []
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jug_id = row['Jugador'].replace(' ', '_').lower()
            ruta_libro = ROOT_DIR / "participantes" / jug_id / "estadisticas" / "historial_puntos.json"
            ruta_base = ROOT_DIR / "participantes" / jug_id / "pronosticos" / "grupos" / f"{jug_id}_base.json"
            
            libro = cargar_json(ruta_libro) or {}
            base_pred = cargar_json(ruta_base) or {}
            
            premios = libro.get("premios_finales", {}).get("formularios", {}).get("detalles", {})
            pts_extra_totales = float(row.get('Puntos_Podio', 0)) + float(row.get('Puntos_Forms', 0))
            
            total_1x2 = total_exactos = 0
            for p_data in libro.get("desglose_partidos", {}).values():
                if p_data.get("acierto_1x2"): total_1x2 += 1
                if p_data.get("acierto_exacto"): total_exactos += 1
                
            victorias_j = derrotas_j = 0
            for j_data in libro.get("desglose_jornadas", {}).values():
                res = j_data.get("resultado")
                if res == "Ganador": victorias_j += 1
                elif res == "Perdedor": derrotas_j += 1
                
            pos_pred = calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
            pasan_pred = base_pred.get("clasificados_a_dieciseisavos", [])
            aciertos_pase = sum(1 for eq in pasan_real if eq in pasan_pred)
            aciertos_pos = sum(1 for eq in pasan_real if eq in pasan_pred and pos_pred.get(eq) == pos_real.get(eq))

            jugadores_datos.append({
                "pos_csv": row['Posicion'],
                "nombre": row['Jugador'],
                "id": jug_id,
                "total": row['TOTAL'],
                "sd_str": f"+{premios.get('sorpresa', 0)} | +{premios.get('decepcion', 0)}",
                "extras": f"{pts_extra_totales:.2f}",
                "aciertos_str": f"{total_exactos} / {total_1x2}",
                "record_str": f"{victorias_j}W - {derrotas_j}L",
                "pase_str": f"{aciertos_pos} / {aciertos_pase}",
                "libro": libro
            })

    html += """
        <details open>
            <summary><h2>📊 Resumen General</h2></summary>
            <div class="table-wrapper">
                <table>
                    <tr>
                        <th>Pos</th><th>Jugador</th><th>Aciertos<br><span style="font-size:0.8em">(Exactos / 1x2)</span></th>
                        <th>Pase a Elim.<br><span style="font-size:0.8em">(Posición / Pasan)</span></th>
                        <th>Sorpresa | Decepción</th><th>Extras<br>(Premios)</th><th>Récord<br>(Ganador/Perdedor)</th><th>Total</th>
                    </tr>
"""
    for j in jugadores_datos:
        pos_display = j['pos_csv'] + "º"
        if j['pos_csv'] == "1": pos_display = "🥇 1º"
        elif j['pos_csv'] == "2": pos_display = "🥈 2º"
        elif j['pos_csv'] == "3": pos_display = "🥉 3º"
        
        html += f"""
                    <tr>
                        <td>{pos_display}</td>
                        <td><a href="participantes/{j['id']}/vistas/dashboard.html" style="color:var(--gold); font-weight:bold; text-decoration:none;">{j['nombre']}</a></td>
                        <td>{j['aciertos_str']}</td>
                        <td>{j['pase_str']}</td>
                        <td>{j['sd_str']}</td>
                        <td>{j['extras']}</td>
                        <td>{j['record_str']}</td>
                        <td class="pts-totales">{j['total']}</td>
                    </tr>"""
    html += """
                </table>
            </div>
        </details>

        <details open>
            <summary><h2>📅 Rendimiento por Jornadas</h2></summary>
            <div class="table-wrapper">
                <table>
                    <tr>
                        <th>Pos</th><th>Jugador</th>
"""
    for j_key in jornadas_keys: html += f"<th>{j_key.upper()}</th>"
    html += "</tr>\n"

    for j in jugadores_datos:
        html += f"<tr><td>{j['pos_csv']}º</td><td>{j['nombre']}</td>"
        desglose_j = j['libro'].get("desglose_jornadas", {})
        desglose_p = j['libro'].get("desglose_partidos", {})
        
        for j_key in jornadas_keys:
            info_j = desglose_j.get(j_key)
            if not info_j:
                html += "<td>-</td>"
                continue
                
            exactos_j = pts_partidos_j = 0
            for p in jornadas_dict.get(j_key, []):
                clave_p = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                info_partido = desglose_p.get(clave_p, {})
                if info_partido.get("acierto_exacto", False): exactos_j += 1
                pts_partidos_j += info_partido.get("puntos_conseguidos", 0)
                
            aciertos_1x2_j = info_j.get("aciertos_1x2", 0)
            pts_totales_j = pts_partidos_j + info_j.get("puntos_bono", 0)
            
            pts_str = f"+{pts_totales_j}" if pts_totales_j > 0 else f"{pts_totales_j}"
            texto_celda = f"<strong>{exactos_j} / {aciertos_1x2_j}</strong><br><span style='font-size:0.85em; font-weight:normal; opacity:0.85;'>{pts_str} pts</span>"
            
            res = info_j.get("resultado", "")
            clase_css = ' class="ganador-jornada"' if res == "Ganador" else (' class="perdedor-jornada"' if res == "Perdedor" else "")
            
            html += f"<td{clase_css}>{texto_celda}</td>"
            
        html += "</tr>\n"
        
    html += """
                </table>
            </div>
        </details>
    </div>
</body>
</html>
"""
    with open(ROOT_DIR / "index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    return True

# =====================================================================
# PÁGINA 2: PARTICIPANTES
# =====================================================================
def generar_participantes_html():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Participantes - Porra Mundial</title>
    <link rel="stylesheet" href="theme.css">
</head>
<body>
    {get_sidebar_html("")}
    <header>
        <h1>👥 Participantes</h1>
        <p>Dashboards Individuales y Gráficos de Rendimiento</p>
    </header>
    <div class="container">
        <div class="jugadores-grid">
"""
    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        html += f"""
            <a href="participantes/{jugador_dir.name}/vistas/dashboard.html" class="card">
                <h3>{nombre}</h3>
                <p>Ver Gráficas y Detalle 📊</p>
            </a>"""
            
    html += """
        </div>
    </div>
</body>
</html>
"""
    with open(ROOT_DIR / "participantes.html", 'w', encoding='utf-8') as f:
        f.write(html)


# =====================================================================
# PÁGINA 3: CALENDARIO OFICIAL (MODO BRACKET CENTRADO Y GRUPOS ANCHOS)
# =====================================================================
def render_partido_bracket(p):
    """Genera la caja HTML de un partido individual para el bracket"""
    loc = p.get('local', 'TBD')
    vis = p.get('visitante', 'TBD')
    gl = p.get('goles_local', '-')
    gv = p.get('goles_visitante', '-')
    ganador = p.get('ganador') if 'ganador' in p else p.get('pasa', 'TBD')
    
    c_loc = "winner" if ganador == loc and ganador != "TBD" else ""
    c_vis = "winner" if ganador == vis and ganador != "TBD" else ""
    
    return f"""
    <div class='bracket-match'>
        <div class='bracket-team {c_loc}'><span class='team-name' title='{loc}'>{loc}</span> <span class='team-score'>{gl}</span></div>
        <div class='bracket-team {c_vis}'><span class='team-name' title='{vis}'>{vis}</span> <span class='team-score'>{gv}</span></div>
    </div>"""

def generar_calendario_html():
    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendario - Porra Mundial</title>
    <link rel="stylesheet" href="theme.css">
</head>
<body>
    {get_sidebar_html("")}
    <header>
        <h1>📅 Calendario Oficial</h1>
        <p>Resultados y Cuadro de Eliminatorias en Tiempo Real</p>
    </header>
    <div class="container">
"""
    # 1. FASE DE GRUPOS (Clase groups-grid)
    fase_grupos = realidad_dict.get("fase_grupos", {})
    if fase_grupos:
        html += "<details open><summary><h2>🌍 Fase de Grupos</h2></summary><div class='groups-grid'>"
        for grupo, partidos in sorted(fase_grupos.items()):
            html += f"""
            <div class="card" style="padding:15px; cursor:default;">
                <h3 style="color:var(--gold); border-bottom:1px solid #333; padding-bottom:5px;">{grupo}</h3>
                <table style="width:100%; font-size:0.9em; margin-top:10px;">"""
            for p in partidos:
                gl = p.get('goles_local', '-')
                gv = p.get('goles_visitante', '-')
                est = "⏳" if p.get('estado') == "notstarted" else "✅"
                html += f"<tr><td style='text-align:right; border:none; padding:5px;'>{p['local']}</td><td style='border:none; font-weight:bold; padding:5px;'>{gl} - {gv}</td><td style='text-align:left; border:none; padding:5px;'>{p['visitante']}</td><td style='border:none;'>{est}</td></tr>"
            html += "</table></div>"
        html += "</div></details>"

    # 2. ELIMINATORIAS (Bracket Lados al Centro)
    eliminatorias = realidad_dict.get("eliminatorias", {})
    if eliminatorias:
        html += "<details open><summary><h2>⚔️ Cuadro de Eliminatorias</h2></summary>"
        html += "<div class='bracket-wrapper'><div class='bracket'>"
        
        # --- LADO IZQUIERDO ---
        html += "<div class='bracket-side left-side'>"
        fases_izq = [("dieciseisavos", "1/16"), ("octavos", "1/8"), ("cuartos", "1/4"), ("semifinales", "Semis")]
        for clave, nombre in fases_izq:
            partidos = eliminatorias.get(clave, [])
            if not partidos and clave == "dieciseisavos": continue
            mitad = (len(partidos) + 1) // 2  # Extrae la primera mitad del array
            partidos_lado = partidos[:mitad] if partidos else []
            
            if partidos_lado:
                html += f"<div class='bracket-round'><div class='round-title'>{nombre}</div>"
                for p in partidos_lado: html += render_partido_bracket(p)
                html += "</div>"
        html += "</div>"

        # --- CENTRO (FINAL ARRIBA, 3º PUESTO ABAJO) ---
        html += "<div class='bracket-center'>"
        
        final = eliminatorias.get("final", [])
        html += "<div class='center-round'><div class='round-title' style='color:var(--gold);'>🏆 FINAL</div>"
        for p in final: html += render_partido_bracket(p)
        html += "</div>"
        
        tercer = eliminatorias.get("tercer_puesto", [])
        if tercer:
            html += "<div class='center-round' style='margin-top:auto;'><div class='round-title' style='color:#a9b7c6;'>🥉 3º Puesto</div>"
            for p in tercer: html += render_partido_bracket(p)
            html += "</div>"
            
        html += "</div>"

        # --- LADO DERECHO (Orden Inverso para simetría visual) ---
        html += "<div class='bracket-side right-side'>"
        fases_der = [("semifinales", "Semis"), ("cuartos", "1/4"), ("octavos", "1/8"), ("dieciseisavos", "1/16")]
        for clave, nombre in fases_der:
            partidos = eliminatorias.get(clave, [])
            if not partidos and clave == "dieciseisavos": continue
            mitad = (len(partidos) + 1) // 2  # Extrae la segunda mitad del array
            partidos_lado = partidos[mitad:] if partidos else []
            
            if partidos_lado:
                html += f"<div class='bracket-round'><div class='round-title'>{nombre}</div>"
                for p in partidos_lado: html += render_partido_bracket(p)
                html += "</div>"
        html += "</div>"
        
        html += "</div></div></details>"

    html += "</div></body></html>"
    with open(ROOT_DIR / "calendario.html", 'w', encoding='utf-8') as f:
        f.write(html)


# =====================================================================
# DASHBOARDS PERSONALES
# =====================================================================
def generar_dashboards_html():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        libro = cargar_json(jugador_dir / "estadisticas" / "historial_puntos.json")
        if not libro: continue
        
        posicion = libro.get("posicion_final_ranking", "-")
        pts_totales = libro.get("puntos_totales", 0)
        
        dir_vistas = jugador_dir / "vistas"
        dir_vistas.mkdir(parents=True, exist_ok=True)
        
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil de {nombre}</title>
    <link rel="stylesheet" href="../../../theme.css">
</head>
<body>
    {get_sidebar_html("../../../")}
    <header>
        <h1>👤 Dashboard: {nombre}</h1>
        <p>Posición Actual: <strong>{posicion}º</strong> | Puntos Totales: <strong style="color:var(--gold); font-size:1.2em;">{pts_totales}</strong></p>
    </header>
    <div class="container">
        
        <details open>
            <summary><h2>🎯 Matriz de Sorpresas y Decepciones</h2></summary>
            <div class="table-wrapper">
                <table>
                    <tr>
                        <th>Selección</th>
                        <th>Gráfico de Desviación</th>
                        <th>Datos (Tú / Media / Real)</th>
                        <th>Resultado</th>
                    </tr>
"""
        matriz_sd = libro.get("matriz_sorpresas_decepciones", {})
        if matriz_sd:
            for eq, datos in sorted(matriz_sd.items()):
                P, M, R = datos["pronostico"], datos["media_grupo"], datos["realidad"]
                puntos, res_txt = datos["puntos"], datos["resultado_calculo"]
                
                estado_html = f"<span style='color:gray;'>Sin Premio</span><br>({puntos} pts)"
                if res_txt == "Sorpresa": estado_html = f"<span class='ganador-jornada'>🔥 +{puntos} Pts<br>¡Sorpresa!</span>"
                elif res_txt == "Decepción": estado_html = f"<span class='perdedor-jornada'>📉 +{puntos} Pts<br>¡Decepción!</span>"
                
                img_name = limpiar_nombre_archivo(eq)
                html += f"""
                    <tr>
                        <td style="font-weight:bold;">{eq}</td>
                        <td><img src="../estadisticas/graficos_sd/{img_name}" class="img-fluid" alt="Gráfico {eq}" onerror="this.style.display='none'"></td>
                        <td style="font-size:0.9em; text-align:left; padding-left:20px;">
                            Tú: <strong>{P}</strong><br>Media: {M}<br>Real: {R}
                        </td>
                        <td>{estado_html}</td>
                    </tr>"""
        else:
            html += "<tr><td colspan='4'>Aún no hay datos de varianza calculados.</td></tr>"
            
        html += """
                </table>
            </div>
        </details>
    </div>
</body>
</html>
"""
        with open(dir_vistas / "dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html)

def ejecutar_07b():
    print("=======================================================")
    print(" 🌐 [07B] INICIANDO RENDERIZADO HTML FRONTEND 🌐")
    print("=======================================================")
    generar_participantes_html()
    print("✅ participantes.html generado.")
    generar_calendario_html()
    print("✅ calendario.html (Resultados Reales y Cuadro) generado.")
    
    if generar_index_html():
        print("✅ index.html global generado con éxito.")
        generar_dashboards_html()
        print("✅ Dashboards HTML enlazados y generados.")
    else:
        print("❌ Error: No se encontró el ranking_oficial.csv")

if __name__ == "__main__":
    ejecutar_07b()