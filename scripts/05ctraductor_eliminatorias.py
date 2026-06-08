import sys
import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def obtener_clasificados(fase_grupos):
    """Calcula los 1º, 2º y los mejores 3º de cada grupo."""
    posiciones = html_utils.calcular_clasificacion_grupos(fase_grupos)
    
    # Agrupar equipos por grupo y ordenarlos por posición
    grupos_ordenados = {}
    for grupo, partidos in fase_grupos.items():
        equipos = set([p['local'] for p in partidos] + [p['visitante'] for p in partidos])
        eq_ordenados = sorted(list(equipos), key=lambda x: posiciones.get(x, 99))
        grupos_ordenados[grupo[-1]] = eq_ordenados # Guardamos con la letra del grupo: 'A', 'B', etc.
        
    return grupos_ordenados

def resolver_terceros(mejores_8_terceros, matriz_fifa):
    """
    Aquí cruzaremos las letras de los 8 grupos clasificados 
    con la matriz de 495 combinaciones de la FIFA.
    Devuelve un diccionario { "3A": "País X", "3C": "País Y" ... }
    """
    # TODO: Implementar cruce con config/matriz_terceros.json
    pass

def traducir_cuadro():
    print("=======================================================")
    print(" 🔄 [05C] TRADUCIENDO PLACEHOLDERS DEL CUADRO 🔄")
    print("=======================================================")
    
    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    realidad = html_utils.cargar_json(ruta_realidad)
    if not realidad: return
    
    # 1. RESOLVER FASE DE GRUPOS (Si todos están 'finished')
    todos_terminados = all(p['estado'] == 'finished' for pts in realidad.get("fase_grupos", {}).values() for p in pts)
    
    diccionario_traduccion = {}
    
    if todos_terminados:
        grupos_ord = obtener_clasificados(realidad["fase_grupos"])
        for letra, equipos in grupos_ord.items():
            if len(equipos) >= 1: diccionario_traduccion[f"1{letra}"] = equipos[0]
            if len(equipos) >= 2: diccionario_traduccion[f"2{letra}"] = equipos[1]
            
        # TODO: Añadir al diccionario los 8 mejores terceros resolviendo la matriz
        
    # 2. RESOLVER ELIMINATORIAS (Ganadores y Perdedores)
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            if p.get("estado") == "finished" and p.get("pasa") != "TBD":
                id_p = p.get("id_partido")
                ganador = p["pasa"]
                perdedor = p["local"] if p["visitante"] == ganador else p["visitante"]
                
                diccionario_traduccion[f"Ganador {id_p}"] = ganador
                diccionario_traduccion[f"Perdedor {id_p}"] = perdedor

    # 3. APLICAR TRADUCCIÓN AL JSON
    reemplazos = 0
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            # Reemplazo de Local
            if p["local"] in diccionario_traduccion:
                p["local"] = diccionario_traduccion[p["local"]]
                reemplazos += 1
            # Reemplazo de Visitante
            elif p["local"].startswith("3") and "3" in p["local"]: # Detecta formato 3A/3B/3C
                pass # Aquí se inyectarán los terceros
                
            if p["visitante"] in diccionario_traduccion:
                p["visitante"] = diccionario_traduccion[p["visitante"]]
                reemplazos += 1
            elif p["visitante"].startswith("3") and "3" in p["visitante"]:
                pass

    if reemplazos > 0:
        with open(ruta_realidad, 'w', encoding='utf-8') as f:
            json.dump(realidad, f, ensure_ascii=False, indent=4)
        print(f"✅ Se han resuelto {reemplazos} equipos en el cuadro eliminatorio.")
    else:
        print("ℹ️ No hay nuevos cruces que resolver por ahora.")

if __name__ == "__main__":
    traducir_cuadro()