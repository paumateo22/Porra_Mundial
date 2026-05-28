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
        print("❌ Error: No existe el ranking_oficial.csv. Ejecuta el motor 06 primero.")
        return False

    ranking = []
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ranking.append(row)

    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Construir el contenido Markdown
    md = f"""# 🏆 Clasificación Oficial - Porra Mundial 2026 🏆
    
*Última actualización: {fecha_act}*

Bienvenidos al panel oficial de la Porra. Aquí podéis consultar la clasificación general en tiempo real. 
Para ver el desglose exacto de tus puntos, entra en tu carpeta personal dentro de `participantes/`.

### 📊 Ranking General

| Pos | Jugador | Pts Base (Part+Jorn) | Pts Grupos | Pts Podio+Extra | **TOTAL** |
| :---: | :--- | :---: | :---: | :---: | :---: |
"""
    # Rellenar la tabla
    for jug in ranking:
        pos = jug['Posicion']
        # Medallas para el podio
        if pos == "1": pos = "🥇 1º"
        elif pos == "2": pos = "🥈 2º"
        elif pos == "3": pos = "🥉 3º"
        else: pos = f"{pos}º"

        nombre = f"**[{jug['Jugador']}](participantes/{jug['Jugador'].replace(' ', '_').lower()}/README.md)**"
        
        pts_base = float(jug['Puntos_Partidos']) + float(jug['Puntos_Jornadas'])
        pts_grupos = jug['Puntos_Grupos']
        pts_extra = float(jug['Puntos_Podio']) + float(jug['Puntos_Forms'])
        total = jug['TOTAL']

        md += f"| {pos} | {nombre} | {pts_base:.2f} | {pts_grupos} | {pts_extra:.2f} | **{total}** |\n"

    md += """
---
*🤖 Sistema automatizado de puntuación desarrollado en Python.*
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

        # Construir Markdown Personal
        md = f"""# 👤 Perfil de Jugador: {nombre}
### Posición Actual: **{posicion}º** | Puntos Totales: **{total}**

---

## 📈 Resumen de Rendimiento
"""
        # Desglose de Jornadas (Últimas 5)
        md += "### 📅 Racha en Jornadas\n"
        jornadas = libro.get("desglose_jornadas", {})
        if jornadas:
            for j, info in jornadas.items():
                if isinstance(info, dict):
                    icono = "✅" if info["resultado"] == "Ganador" else ("❌" if info["resultado"] == "Perdedor" else "➖")
                    md += f"- **{j}:** {info['aciertos_1x2']} aciertos | Bono: {info['puntos_bono']} pts {icono}\n"
        else:
            md += "*Aún no hay datos de jornadas.*\n"

        # Resoluciones Finales
        md += "\n### 🏆 Premios a Largo Plazo\n"
        grupos = libro.get("resolucion_fase_grupos", {})
        if grupos:
            md += f"- **Aciertos Fase de Grupos:** {grupos.get('puntos_conseguidos', 0)} pts\n"

        premios = libro.get("premios_finales", {})
        if premios:
            md += f"- **Podio Acertado:** {premios.get('podio', {}).get('puntos_conseguidos', 0)} pts\n"
            md += f"- **Formularios Extra:** {premios.get('formularios', {}).get('puntos_conseguidos', 0)} pts\n"

        md += "\n---\n*Para consultar el desglose exacto partido a partido, abre tu archivo `estadisticas/historial_puntos.json`.*"
        md += "\n\n[⬅️ Volver a la clasificación general](../../README.md)"

        # Guardar en la carpeta del jugador
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