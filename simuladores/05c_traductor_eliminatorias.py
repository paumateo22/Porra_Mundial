import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def calcular_clasificacion_estricta(partidos_grupo):
    """
    Calcula Puntos, Diferencia de Goles y Goles a Favor.
    Retorna la lista de equipos ordenados. Emite aviso si persiste empate.
    """
    tabla = {}
    for p in partidos_grupo:
        loc, vis = p['local'], p['visitante']
        if loc not in tabla: tabla[loc] = {"pts": 0, "gd": 0, "gf": 0}
        if vis not in tabla: tabla[vis] = {"pts": 0, "gd": 0, "gf": 0}
        
        if p['estado'] != 'finished': continue
            
        gl = int(p.get('goles_local', 0)) if str(p.get('goles_local', '')).isdigit() else 0
        gv = int(p.get('goles_visitante', 0)) if str(p.get('goles_visitante', '')).isdigit() else 0
        
        tabla[loc]["gf"] += gl
        tabla[vis]["gf"] += gv
        tabla[loc]["gd"] += (gl - gv)
        tabla[vis]["gd"] += (gv - gl)
        
        if gl > gv: tabla[loc]["pts"] += 3
        elif gv > gl: tabla[vis]["pts"] += 3
        else: tabla[loc]["pts"] += 1; tabla[vis]["pts"] += 1

    # Ordenamiento FIFA: Puntos > GD > GF
    equipos_ord = sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]), reverse=True)
    
    # Comprobar si hay empate matemático total en las posiciones de corte
    if len(equipos_ord) >= 2:
        eq1, st1 = equipos_ord[0]
        eq2, st2 = equipos_ord[1]
        if (st1["pts"], st1["gd"], st1["gf"]) == (st2["pts"], st2["gd"], st2["gf"]):
            print(f"⚠️ EMPATE TOTAL: {eq1} y {eq2} están empatados a todo. Resolución Manual requerida.")

    return [{"equipo": eq, "stats": stats} for eq, stats in equipos_ord]

def traducir_cuadro():
    print("=======================================================")
    print(" 🔄 [05C] TRADUCIENDO PLACEHOLDERS DEL CUADRO 🔄")
    print("=======================================================")
    
    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    ruta_matriz = ROOT_DIR / "config" / "matriz_terceros.json"
    
    realidad = html_utils.cargar_json(ruta_realidad)
    matriz = html_utils.cargar_json(ruta_matriz)
    
    if not realidad or not matriz:
        print("❌ Error: Faltan archivos base (realidad_oficial.json o matriz_terceros.json).")
        return
        
    todos_terminados = all(p['estado'] == 'finished' for pts in realidad.get("fase_grupos", {}).values() for p in pts)
    
    diccionario_traduccion = {}
    
    if todos_terminados:
        lista_terceros = []
        
        for nombre_grupo, partidos in realidad.get("fase_grupos", {}).items():
            letra_grupo = nombre_grupo[-1] # Ej: "Grupo A" -> "A"
            clasificacion = calcular_clasificacion_estricta(partidos)
            
            if len(clasificacion) >= 1: diccionario_traduccion[f"1{letra_grupo}"] = clasificacion[0]["equipo"]
            if len(clasificacion) >= 2: diccionario_traduccion[f"2{letra_grupo}"] = clasificacion[1]["equipo"]
            if len(clasificacion) >= 3: 
                lista_terceros.append({
                    "letra": letra_grupo,
                    "equipo": clasificacion[2]["equipo"],
                    "stats": clasificacion[2]["stats"]
                })
        
        # Determinar los 8 mejores terceros
        lista_terceros_ord = sorted(lista_terceros, key=lambda x: (x["stats"]["pts"], x["stats"]["gd"], x["stats"]["gf"]), reverse=True)
        mejores_8 = lista_terceros_ord[:8]
        
        # Crear la llave de búsqueda combinando sus letras ordenadas alfabéticamente
        letras_clasificados = sorted([t["letra"] for t in mejores_8])
        llave_matriz = "".join(letras_clasificados)
        
        cruce_terceros = matriz.get(llave_matriz, {})
        
        if not cruce_terceros:
            print(f"❌ Error: La combinación de terceros '{llave_matriz}' no existe en la matriz.")
        else:
            # Añadir los 8 terceros al diccionario de traducción usando su ID real "3X"
            mapeo_terceros_equipos = {f"3{t['letra']}": t["equipo"] for t in mejores_8}
            for t_k, t_eq in mapeo_terceros_equipos.items():
                diccionario_traduccion[t_k] = t_eq
                
            # Mapeamos contra quién juegan los primeros
            # Si cruce_terceros dice "1A": "3E", asociamos esa búsqueda para facilitar la traducción
            for primero, tercero_rival in cruce_terceros.items():
                diccionario_traduccion[f"RivalTercero_{primero}"] = mapeo_terceros_equipos[tercero_rival]
                
    # 2. RESOLVER ELIMINATORIAS (Ganadores de cruces previos)
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            if p.get("estado") == "finished" and p.get("pasa") and p.get("pasa") != "TBD":
                id_p = p.get("id_partido")
                ganador = p["pasa"]
                perdedor = p["local"] if p["visitante"] == ganador else p["visitante"]
                
                diccionario_traduccion[f"Ganador {id_p}"] = ganador
                diccionario_traduccion[f"Perdedor {id_p}"] = perdedor

    # 3. APLICAR BARRIDO AL JSON
    reemplazos = 0
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            # Reemplazo directo (1A, 2B, Ganador X)
            if p["local"] in diccionario_traduccion:
                p["local"] = diccionario_traduccion[p["local"]]
                reemplazos += 1
                
            if p["visitante"] in diccionario_traduccion:
                p["visitante"] = diccionario_traduccion[p["visitante"]]
                reemplazos += 1
                
            # Reemplazo complejo de terceros
            # Si el visitante es un placeholder raro (ej: 3A/3B/3C...) y el local era un primero
            if "3" in p["visitante"] and "/" in p["visitante"]:
                # Buscamos en el archivo base de cruces quién es el local original de este partido
                local_original = None
                if p["id_partido"] == 73: local_original = "1E"
                elif p["id_partido"] == 74: local_original = "1I"
                elif p["id_partido"] == 77: local_original = "1I" # Revisar si este o el 74 es 1I según matriz final
                elif p["id_partido"] == 79: local_original = "1D"
                elif p["id_partido"] == 80: local_original = "1G"
                elif p["id_partido"] == 83: local_original = "1A"
                elif p["id_partido"] == 84: local_original = "1L"
                elif p["id_partido"] == 87: local_original = "1B"
                elif p["id_partido"] == 88: local_original = "1K"
                
                if local_original and f"RivalTercero_{local_original}" in diccionario_traduccion:
                    p["visitante"] = diccionario_traduccion[f"RivalTercero_{local_original}"]
                    reemplazos += 1

    if reemplazos > 0:
        with open(ruta_realidad, 'w', encoding='utf-8') as f:
            json.dump(realidad, f, ensure_ascii=False, indent=4)
        print(f"✅ Se han resuelto {reemplazos} equipos en el cuadro eliminatorio.")
    else:
        print("ℹ️ No hay nuevos cruces que resolver por ahora.")

if __name__ == "__main__":
    traducir_cuadro()