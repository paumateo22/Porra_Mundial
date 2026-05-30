import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def formatear_resultado(p):
    """Formatea el resultado de los goles, incluyendo penaltis si hubo empate."""
    gl = str(p.get("goles_local", "-"))
    gv = str(p.get("goles_visitante", "-"))
    
    # Si hay goles y es un empate, buscamos penaltis
    if gl.isdigit() and gv.isdigit() and gl == gv:
        pl = str(p.get("penaltis_local", ""))
        pv = str(p.get("penaltis_visitante", ""))
        if pl.isdigit() and pv.isdigit():
            return f"**{gl}** ({pl}) - ({pv}) **{gv}**"
    
    return f"**{gl}** - **{gv}**"

def calcular_clasificacion_grupo(partidos_grupo):
    """Calcula la tabla de posiciones con todos los detalles (PJ, PG, PE, PP, GF, GC, DIF, PTS)."""
    tabla = {}
    for p in partidos_grupo:
        loc, vis = p.get('local', 'L'), p.get('visitante', 'V')
        if loc not in tabla: tabla[loc] = {"pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "dif": 0, "pts": 0}
        if vis not in tabla: tabla[vis] = {"pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "dif": 0, "pts": 0}

        gl_str, gv_str = str(p.get('goles_local', '')), str(p.get('goles_visitante', ''))
        if gl_str.isdigit() and gv_str.isdigit():
            gl, gv = int(gl_str), int(gv_str)
            
            tabla[loc]["pj"] += 1
            tabla[vis]["pj"] += 1
            tabla[loc]["gf"] += gl
            tabla[loc]["gc"] += gv
            tabla[vis]["gf"] += gv
            tabla[vis]["gc"] += gl
            tabla[loc]["dif"] += (gl - gv)
            tabla[vis]["dif"] += (gv - gl)

            if gl > gv:
                tabla[loc]["pts"] += 3; tabla[loc]["pg"] += 1; tabla[vis]["pp"] += 1
            elif gv > gl:
                tabla[vis]["pts"] += 3; tabla[vis]["pg"] += 1; tabla[loc]["pp"] += 1
            else:
                tabla[loc]["pts"] += 1; tabla[vis]["pts"] += 1
                tabla[loc]["pe"] += 1; tabla[vis]["pe"] += 1

    # Ordenar: Puntos > Diferencia > Goles a Favor
    return sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"], x[1]["gf"]), reverse=True)

def generar_readme_grupos(jugador_dir, nombre):
    nombre_id = jugador_dir.name
    ruta_json = jugador_dir / "pronosticos" / "grupos" / f"{nombre_id}_base.json"
    if not ruta_json.exists(): return

    datos = cargar_json(ruta_json)
    if not datos: return

    clasificados = datos.get("clasificados_a_dieciseisavos", [])
    fase_grupos = datos.get("fase_grupos", {})

    md = f"# 🌍 Pronóstico Fase de Grupos - {nombre}\n\n"
    md += "Aquí puedes consultar las clasificaciones exactas que predijo el jugador antes de empezar el torneo.\n\n"
    md += "---\n\n"

    for grupo, partidos in fase_grupos.items():
        nombre_grupo = grupo.replace('_', ' ').upper()
        md += f"## 📊 {nombre_grupo}\n"
        
        # Tabla de Posiciones
        md += "| Pos | Equipo | PJ | PG | PE | PP | GF | GC | DIF | PTS | Pase |\n"
        md += "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        
        posiciones = calcular_clasificacion_grupo(partidos)
        for idx, (eq, stats) in enumerate(posiciones):
            pos_str = f"**{idx + 1}º**"
            pasa = "✅" if eq in clasificados else "❌"
            md += f"| {pos_str} | **{eq}** | {stats['pj']} | {stats['pg']} | {stats['pe']} | {stats['pp']} | {stats['gf']} | {stats['gc']} | {stats['dif']} | **{stats['pts']}** | {pasa} |\n"
        
        md += "\n<details><summary><b>Ver Partidos del Grupo</b></summary>\n\n"
        md += "| Local | Resultado | Visitante |\n"
        md += "| :--- | :---: | :--- |\n"
        for p in partidos:
            res = formatear_resultado(p)
            md += f"| {p.get('local', '-')} | {res} | {p.get('visitante', '-')} |\n"
        md += "\n</details>\n\n---\n"

    ruta_md = jugador_dir / "pronosticos" / "grupos" / "README.md"
    with open(ruta_md, 'w', encoding='utf-8') as f:
        f.write(md)

def generar_readme_eliminatorias(jugador_dir, nombre):
    fases = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
    
    for fase in fases:
        ruta_carpeta = jugador_dir / "pronosticos" / "eliminatorias" / fase
        ruta_json = ruta_carpeta / f"{fase}.json"
        
        if not ruta_json.exists(): continue
        
        datos = cargar_json(ruta_json)
        predicciones = datos.get("predicciones", {}) if datos else {}
        if not predicciones: continue

        md = f"# ⚔️ Cuadro Predictivo desde {fase.capitalize()} - {nombre}\n\n"
        md += f"Esta es la hoja de ruta que imaginó el jugador cuando arrancaron los {fase.capitalize()}.\n\n"
        md += "---\n\n"

        # Añadimos "finales" a la lista para que coincida con tu JSON
        orden_logico = ["dieciseisavos", "octavos", "cuartos", "semifinales", "tercer_puesto", "final", "finales"]
        
        for sub_fase in orden_logico:
            if sub_fase in predicciones:
                nombre_sub_fase = sub_fase.replace("_", " ").upper()
                partidos = predicciones[sub_fase]
                
                md += f"### 🏆 {nombre_sub_fase}\n"
                md += "| Local | Resultado | Visitante | Avanza |\n"
                md += "| :--- | :---: | :--- | :---: |\n"
                
                for p in partidos:
                    res = formatear_resultado(p)
                    # Quien avanza visualmente
                    avanza = p.get("pasa", p.get("ganador", "-"))
                    md += f"| **{p.get('local', '-')}** | {res} | **{p.get('visitante', '-')}** | 🟢 {avanza} |\n"
                md += "\n"

        ruta_md = ruta_carpeta / "README.md"
        with open(ruta_md, 'w', encoding='utf-8') as f:
            f.write(md)
            
def generar_readmes_pronosticos():
    print("=======================================================")
    print(" 🎨 [09] GENERANDO MUSEOS DE PRONÓSTICOS (CARPETAS LOCALES) ")
    print("=======================================================")
    
    dir_participantes = ROOT_DIR / "participantes"
    if not dir_participantes.exists(): return
    
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        generar_readme_grupos(jugador_dir, nombre)
        generar_readme_eliminatorias(jugador_dir, nombre)
        
    print("✅ Vistas de pronósticos internos generadas con éxito.")

if __name__ == "__main__":
    generar_readmes_pronosticos()