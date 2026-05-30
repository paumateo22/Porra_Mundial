import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

def formatear_resultado(p):
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

def generar_readme_grupos(jugador_dir, nombre, dict_reales):
    nombre_id = jugador_dir.name
    ruta_json = jugador_dir / "pronosticos" / "grupos" / f"{nombre_id}_base.json"
    if not ruta_json.exists(): return

    datos = cargar_json(ruta_json)
    if not datos: return

    clasificados = datos.get("clasificados_a_dieciseisavos", [])
    fase_grupos = datos.get("fase_grupos", {})

    md = f"# 🌍 Pronóstico Inicial Completo - {nombre}\n\nAquí puedes consultar las tablas y el camino exacto hacia la final que predijo el jugador antes de empezar el torneo.\n\n---\n\n"

    # 1. TABLAS DE GRUPOS ORDENADAS (A -> L)
    for grupo, partidos in sorted(fase_grupos.items()):
        nombre_grupo = grupo.replace('_', ' ').upper()
        md += f"## 📊 {nombre_grupo}\n"
        md += "| Pos | Equipo | PJ | PG | PE | PP | GF | GC | DIF | PTS | Pase |\n"
        md += "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        
        posiciones = calcular_clasificacion_grupo(partidos)
        for idx, (eq, stats) in enumerate(posiciones):
            pos_str, pasa = f"**{idx + 1}º**", ("✅" if eq in clasificados else "❌")
            md += f"| {pos_str} | **{eq}** | {stats['pj']} | {stats['pg']} | {stats['pe']} | {stats['pp']} | {stats['gf']} | {stats['gc']} | {stats['dif']} | **{stats['pts']}** | {pasa} |\n"
        
        # TABLA LADO A LADO CON HTML (Pronóstico vs Real)
        md += "\n<details><summary><b>Ver Partidos del Grupo</b></summary><br>\n\n"
        md += "<table width='100%'>\n<tr><th width='50%' style='text-align:center;'>Tu Pronóstico</th><th width='50%' style='text-align:center;'>Resultado Real</th></tr>\n"
        for p in partidos:
            loc, vis = p.get('local', '-'), p.get('visitante', '-')
            res_pred = formatear_resultado(p)
            
            p_real = dict_reales.get(f"{loc}_vs_{vis}", {})
            res_real = formatear_resultado(p_real) if p_real and p_real.get("estado") == "finished" else "⏳ Pendiente"
                
            md += f"<tr><td align='center'><b>{loc}</b> {res_pred} <b>{vis}</b></td><td align='center'><b>{loc}</b> {res_real} <b>{vis}</b></td></tr>\n"
        md += "</table>\n</details>\n\n---\n"

    # 2. EL ÁRBOL HASTA LA FINAL (Si está en el JSON de grupos)
    eliminatorias = datos.get("eliminatorias", {})
    if eliminatorias:
        md += "\n## ⚔️ Camino a la Final (Pronóstico Original)\n\n"
        orden_logico = ["dieciseisavos", "octavos", "cuartos", "semifinales", "tercer_puesto", "final", "finales"]
        
        for sub_fase in orden_logico:
            partidos_sub = eliminatorias.get(sub_fase, [])
            if partidos_sub:
                md += f"### 🏆 {sub_fase.replace('_', ' ').upper()}\n"
                md += "| Local | Resultado | Visitante | Avanza |\n"
                md += "| :--- | :---: | :--- | :---: |\n"
                for i, p in enumerate(partidos_sub):
                    etiqueta = ""
                    if sub_fase in ["finales", "final", "tercer_puesto"]:
                        etiqueta = "🥉 " if (i == 0 and len(partidos_sub) > 1) or sub_fase == "tercer_puesto" else "🏆 "
                    
                    res = formatear_resultado(p)
                    avanza = p.get("pasa", p.get("ganador", "-"))
                    md += f"| {etiqueta}**{p.get('local', '-')}** | {res} | **{p.get('visitante', '-')}** | 🟢 {avanza} |\n"
                md += "\n"

    with open(jugador_dir / "pronosticos" / "grupos" / "README.md", 'w', encoding='utf-8') as f: f.write(md)

def generar_readme_eliminatorias(jugador_dir, nombre):
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
                md += "| Local | Resultado | Visitante | Avanza |\n"
                md += "| :--- | :---: | :--- | :---: |\n"
                
                for i, p in enumerate(partidos):
                    etiqueta = ""
                    if sub_fase in ["finales", "final", "tercer_puesto"]:
                        etiqueta = "🥉 " if (i == 0 and len(partidos) > 1) or sub_fase == "tercer_puesto" else "🏆 "
                        
                    res = formatear_resultado(p)
                    avanza = p.get("pasa", p.get("ganador", "-"))
                    md += f"| {etiqueta}**{p.get('local', '-')}** | {res} | **{p.get('visitante', '-')}** | 🟢 {avanza} |\n"
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
        generar_readme_grupos(jugador_dir, nombre, dict_reales)
        generar_readme_eliminatorias(jugador_dir, nombre)
        
    print("✅ Vistas de pronósticos internos generadas con éxito.")

if __name__ == "__main__":
    generar_readmes_pronosticos()