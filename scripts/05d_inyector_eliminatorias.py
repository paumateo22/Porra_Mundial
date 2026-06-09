import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def inyectar_eliminatorias():
    print("=======================================================")
    print(" 💉 [05D] INYECTANDO 1/16 DESDE ELIMINATORIAS.TXT 💉")
    print("=======================================================")
    
    txt_path = ROOT_DIR / "eliminatorias.txt"
    json_path = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"

    if not txt_path.exists():
        print("❌ Error: No se encontró el archivo eliminatorias.txt en la raíz.")
        return

    with open(txt_path, 'r', encoding='utf-8') as f:
        contenido = f.read().strip()

    # Separar por comas y limpiar espacios en blanco a los lados de cada nombre
    equipos = [eq.strip() for eq in contenido.split(',') if eq.strip()]

    if len(equipos) != 32:
        print(f"❌ Error crítico: Hay {len(equipos)} equipos en el txt, pero se necesitan exactamente 32.")
        return

    if not json_path.exists():
        print("❌ Error: No se encontró realidad_oficial.json.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        realidad = json.load(f)

    dieciseisavos = realidad.get("eliminatorias", {}).get("dieciseisavos", [])

    if not dieciseisavos or len(dieciseisavos) != 16:
        print("❌ Error: No se encontraron los 16 partidos de dieciseisavos en el JSON.")
        return

    # Asegurarnos de que están ordenados por ID_partido (73 a 88)
    dieciseisavos.sort(key=lambda x: x.get("id_partido", 0))

    eq_idx = 0
    for partido in dieciseisavos:
        partido["local"] = equipos[eq_idx]
        partido["visitante"] = equipos[eq_idx + 1]
        eq_idx += 2

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(realidad, f, ensure_ascii=False, indent=4)

    print("✅ Se han inyectado los 32 equipos en los dieciseisavos con éxito.")

if __name__ == "__main__":
    inyectar_eliminatorias()