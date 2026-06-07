import sys
from pathlib import Path
from turtle import width

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def render_partido_bracket(p):
    loc, vis = p.get('local', 'TBD'), p.get('visitante', 'TBD')
    gl, gv = p.get('goles_local', '-'), p.get('goles_visitante', '-')
    ganador = p.get('ganador') if 'ganador' in p else p.get('pasa', 'TBD')
    c_loc = "winner" if ganador == loc and ganador != "TBD" else ""
    c_vis = "winner" if ganador == vis and ganador != "TBD" else ""
    return f"""
    <div class='bracket-match'>
        <div class='bracket-team {c_loc}'><span class='team-name' title='{loc}'>{loc}</span> <span class='team-score'>{gl}</span></div>
        <div class='bracket-team {c_vis}'><span class='team-name' title='{vis}'>{vis}</span> <span class='team-score'>{gv}</span></div>
    </div>"""

def generar_calendario_html():
    realidad_dict = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendario - Porra Mundial</title>
    <link rel="stylesheet" href="theme.css">
    <style>
        /* Estilos específicos para forzar el bracket al ancho completo */
        .bracket-full-width {{ width: 100%; max-width: 100%; padding: 0 20px; box-sizing: border-box; margin: 30px auto; }}
        .true-bracket {{display:flex;width:100%;justify-content:center;gap:8px;font-size:0.75em;overflow:hidden;padding-bottom:20px;min-height:500px;}}
        .bracket-col-wrapper {{display:flex;flex-direction:column;flex:1;min-width:95px;}}
        .bracket-col {{ display: flex; flex-direction: column; justify-content: space-around; flex: 1; gap: 10px; }}
        .bracket-center-wrapper {{display:flex;flex-direction:column;flex:1.1;min-width:110px;justify-content:center;gap:40px;margin:0 5px;}}
        .bracket-match {{ background: #222; border: 1px solid #444; border-radius: 4px; overflow: hidden; width: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
        .bracket-team {{ display: flex; justify-content: space-between; padding: 5px 8px; border-bottom: 1px solid #333; color: #ccc; align-items: center; }}
        .bracket-team:last-child {{ border-bottom: none; }}
        .bracket-team.winner {{ background: rgba(218, 165, 32, 0.15); color: var(--gold); font-weight: bold; }}
        .team-name {{max-width:70px;}}
        .team-score {{ background: #111; padding: 2px 6px; border-radius: 3px; color: #fff; font-weight: bold; font-size: 0.9em; }}
        .winner .team-score {{ background: var(--gold); color: #000; }}
        .round-header {{ text-align: center; font-weight: bold; color: var(--table-header); margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 5px; text-transform: uppercase; font-size: 0.95em; }}
    </style>
</head>
<body>
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("📅 Calendario Oficial", "Resultados y Cuadro de Eliminatorias en Tiempo Real", "")}
    
    <div class="container">
"""
    # FASE DE GRUPOS
    fase_grupos = realidad_dict.get("fase_grupos", {})
    if fase_grupos:
        html += "<details open><summary><h2>🌍 Fase de Grupos</h2></summary><div class='groups-grid'>"
        for grupo, partidos in sorted(fase_grupos.items()):
            html += f"""<div class="card" style="padding:15px; cursor:default;"><h3 style="color:var(--gold); border-bottom:1px solid #333; padding-bottom:5px;">{grupo}</h3><table style="width:100%; font-size:0.9em; margin-top:10px;">"""
            for p in partidos: 
                gl, gv = p.get('goles_local', '-'), p.get('goles_visitante', '-')
                est = "⏳" if p.get('estado') == "notstarted" else "✅"
                html += f"<tr><td style='text-align:right; border:none; padding:5px; width:40%;'>{p['local']}</td><td style='border:none; font-weight:bold; padding:5px; width:20%; text-align:center;'>{gl} - {gv}</td><td style='text-align:left; border:none; padding:5px; width:40%;'>{p['visitante']}</td><td style='border:none;'>{est}</td></tr>"
            html += "</table></div>"
        html += "</div></details></div>" # Cerramos el .container aquí

    # ELIMINATORIAS (Ancho completo fuera del container)
    eliminatorias = realidad_dict.get("eliminatorias", {})
    if eliminatorias:
        html += "<div class='bracket-full-width'><details open><summary><h2 style='margin-bottom:20px;'>⚔️ Cuadro de Eliminatorias</h2></summary><div class='true-bracket'>"
        
        # LADO IZQUIERDO
        fases_izq = [("dieciseisavos", "1/16"), ("octavos", "1/8"), ("cuartos", "1/4"), ("semifinales", "Semis")]
        for clave, nombre in fases_izq:
            partidos = eliminatorias.get(clave, [])
            if not partidos and clave == "dieciseisavos": continue
            mitad = (len(partidos) + 1) // 2
            partidos_col = partidos[:mitad] if partidos else []
            if partidos_col:
                html += f"<div class='bracket-col-wrapper left-side'><div class='round-header'>{nombre}</div><div class='bracket-col'>"
                for p in partidos_col: html += render_partido_bracket(p)
                html += "</div></div>"
        
        # CENTRO
        html += "<div class='bracket-center-wrapper'>"
        final = eliminatorias.get("final", [])
        html += "<div style='width:100%;'>"
        html += "<div class='round-header' style='color:var(--gold);'>🏆 FINAL</div>"
        for p in final: html += render_partido_bracket(p)
        html += "</div>"
        
        tercer = eliminatorias.get("tercer_puesto", [])
        if tercer:
            html += "<div style='width:100%;'>"
            html += "<div class='round-header' style='color:#a9b7c6;'>🥉 3º Puesto</div>"
            for p in tercer: html += render_partido_bracket(p)
            html += "</div>"
        html += "</div>"
        
        # LADO DERECHO (Mismo orden visual pero converge al centro)
        fases_der = [("semifinales", "Semis"), ("cuartos", "1/4"), ("octavos", "1/8"), ("dieciseisavos", "1/16")]
        for clave, nombre in fases_der:
            partidos = eliminatorias.get(clave, [])
            if not partidos and clave == "dieciseisavos": continue
            mitad = (len(partidos) + 1) // 2
            partidos_col = partidos[mitad:] if partidos else []
            if partidos_col:
                html += f"<div class='bracket-col-wrapper right-side'><div class='round-header'>{nombre}</div><div class='bracket-col'>"
                for p in partidos_col: html += render_partido_bracket(p)
                html += "</div></div>"
                
        html += "</div></details></div>"
        
    html += "</body></html>"
    
    with open(ROOT_DIR / "calendario.html", 'w', encoding='utf-8') as f: 
        f.write(html)
    print("✅ calendario.html generado (modo Bracket completo).")

if __name__ == "__main__":
    generar_calendario_html()