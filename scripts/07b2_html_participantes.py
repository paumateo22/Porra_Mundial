import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

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
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("👥 Participantes", "Dashboards Individuales y Gráficos de Rendimiento", "")}
    <div class="container">
        <div class="jugadores-grid">"""
    for j_dir in jugadores: 
        html += f"""<a href="participantes/{j_dir.name}/vistas/dashboard.html" class="card"><h3>{j_dir.name.replace('_', ' ').title()}</h3><p>Ver Gráficas y Detalle 📊</p></a>"""
    html += "</div></div></body></html>"
    
    with open(ROOT_DIR / "participantes.html", 'w', encoding='utf-8') as f: 
        f.write(html)
    print("✅ participantes.html generado.")

if __name__ == "__main__":
    generar_participantes_html()