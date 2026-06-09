import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def generar_matriz_json():
    ruta_txt = ROOT_DIR / "raw_matriz.txt"
    ruta_json = ROOT_DIR / "config" / "matriz_terceros.json"
    
    if not ruta_txt.exists():
        print("❌ Falla: Guarda las combinaciones en 'raw_matriz.txt'")
        return

    columnas_primeros = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]
    matriz_final = {}

    with open(ruta_txt, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Regex: Busca secuencias exactas de 8 códigos que empiecen por 3 y terminen en letra A-L
    # Ignora automáticamente números de página, textos de cabecera o saltos de línea mal hechos
    patron = r'(3[A-L])\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])'
    matches = re.findall(patron, contenido)

    for terceros in matches:
        # terceros es una tupla de 8 elementos: ('3E', '3J', '3I', ...)
        letras = sorted([t.replace('3', '') for t in terceros])
        llave_combinacion = "".join(letras)
        
        mapeo_cruces = {columnas_primeros[i]: terceros[i] for i in range(8)}
        matriz_final[llave_combinacion] = mapeo_cruces

    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(matriz_final, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Matriz JSON generada con éxito ({len(matriz_final)} combinaciones válidas encontradas).")

if __name__ == "__main__":
    generar_matriz_json()