import sys
import cv2
import easyocr
import json
import numpy as np
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

print("🤖 Cargando modelos de EasyOCR...")
reader_text = easyocr.Reader(['es'], gpu=False)
reader_num = easyocr.Reader(['es'], gpu=False)

FASES_ORDENADAS = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]

def leer_numero_aislado(roi_gol):
    if roi_gol.size == 0: return None
    
    h, w = roi_gol.shape[:2]
    if h > 4 and w > 4:
        roi_gol = roi_gol[2:h-2, 2:w-2]
        
    gris = cv2.cvtColor(roi_gol, cv2.COLOR_BGR2GRAY)
    _, roi_bin = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Ajuste automático por contornos
    contornos, _ = cv2.findContours(roi_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contornos:
        c = max(contornos, key=cv2.contourArea)
        x_c, y_c, w_c, h_c = cv2.boundingRect(c)
        roi_bin = roi_bin[y_c:y_c+h_c, x_c:x_c+w_c]
        
    # =================================================================
    # 🌟 PLAN A: TEMPLATE MATCHING (Más tolerante: 55%)
    # =================================================================
    ruta_plantillas = ROOT_DIR / "templates"
    if ruta_plantillas.exists():
        roi_estandar = cv2.resize(roi_bin, (20, 30), interpolation=cv2.INTER_AREA)
        mejor_score = -1
        numero_detectado = None
        
        for i in range(10):
            ruta_tpl = ruta_plantillas / f"{i}.png"
            if not ruta_tpl.exists(): continue
                
            tpl = cv2.imread(str(ruta_tpl), cv2.IMREAD_GRAYSCALE)
            if tpl is None: continue
            
            _, tpl_bin = cv2.threshold(tpl, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            contornos_tpl, _ = cv2.findContours(tpl_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contornos_tpl:
                c_tpl = max(contornos_tpl, key=cv2.contourArea)
                xt, yt, wt, ht = cv2.boundingRect(c_tpl)
                tpl_bin = tpl_bin[yt:yt+ht, xt:xt+wt]
                
            tpl_estandar = cv2.resize(tpl_bin, (20, 30), interpolation=cv2.INTER_AREA)
            
            resultado = cv2.matchTemplate(roi_estandar, tpl_estandar, cv2.TM_CCOEFF_NORMED)
            score = resultado[0][0]
            
            if score > mejor_score:
                mejor_score = score
                numero_detectado = i
                
        # 🔧 FIX: Bajamos el umbral para que confíe casi siempre en las plantillas
        if mejor_score > 0.55:
            return numero_detectado

    # =================================================================
    # ⚠️ PLAN B: EASYOCR (Solo casos extremos de ruido)
    # =================================================================
    amp = cv2.resize(roi_bin, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    bn_con_marco = cv2.copyMakeBorder(amp, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=0)
    res = reader_num.readtext(bn_con_marco, allowlist='0123456789lI|oO')
    
    if res:
        texto = "".join([t[1] for t in res])
        texto = texto.replace('l', '1').replace('I', '1').replace('|', '1').replace('o', '0').replace('O', '0')
        numeros = ''.join(filter(str.isdigit, texto))
        if numeros:
            return int(numeros[0])
            
    return None

def leer_texto_aislado(roi_texto):
    if roi_texto.size == 0: return "Desconocido"
    
    gris = cv2.cvtColor(roi_texto, cv2.COLOR_BGR2GRAY)
    amp = cv2.resize(gris, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    con_marco = cv2.copyMakeBorder(amp, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    
    res = reader_text.readtext(con_marco)
    if res:
        res_ordenado = sorted(res, key=lambda caja: caja[0][0][0])
        texto_final = " ".join([t[1] for t in res_ordenado]).strip()
        return texto_final.replace('[', '').replace(']', '').replace('|', '').strip()
        
    return "Desconocido"

def extraer_partidos_de_imagen(ruta_imagen):
    img_original = cv2.imread(str(ruta_imagen))
    if img_original is None: return []
    
    img_recortada = img_original[:, 173:]
    ancho = img_recortada.shape[1]
    
    resultados = reader_text.readtext(img_recortada)
    elementos = []
    
    # 🔧 FIX: Lista de basura reducida para no borrar partidos reales por error
    palabras_basura = ['calcular', 'reajustar', 'dieciseisavos', 'octavos', 'cuartos', 'semifinales', 'finales', 'partido por', 'lugar', 'final']

    for bbox, texto, conf in resultados:
        y_centro = (bbox[0][1] + bbox[2][1]) / 2
        texto_limpio = texto.strip().lower()
        if any(basura in texto_limpio for basura in palabras_basura):
            continue
        elementos.append({'y': y_centro})
        
    if not elementos: return []
        
    elementos.sort(key=lambda item: item['y'])
    filas = []
    fila_actual = []
    y_referencia = None
    
    # 🔧 FIX: Aumentamos el margen a 20px para agrupar mejor las filas
    for el in elementos:
        if y_referencia is None or abs(el['y'] - y_referencia) < 20:
            fila_actual.append(el)
        else:
            filas.append(fila_actual)
            fila_actual = [el]
        y_referencia = fila_actual[0]['y']
    if fila_actual: filas.append(fila_actual)
    
    filas_y = [sum(el['y'] for el in fila) / len(fila) for fila in filas]

    partidos_extraidos = []
    print(f"\n--- ⚽ EXTRACCIÓN MILIMÉTRICA: {ruta_imagen.name} ---")
    
    for y_centro in filas_y:
        y1 = int(max(0, y_centro - 15))
        y2 = int(min(img_recortada.shape[0], y_centro + 15))
        
        roi_nombre_loc = img_recortada[y1:y2, 0:170]
        roi_gol_loc    = img_recortada[y1:y2, 200:230]
        roi_gol_vis    = img_recortada[y1:y2, 245:275]
        roi_nombre_vis = img_recortada[y1:y2, 300:ancho]
        
        equipo_local = leer_texto_aislado(roi_nombre_loc)
        equipo_visitante = leer_texto_aislado(roi_nombre_vis)
        
        texto_unido = (equipo_local + " " + equipo_visitante).lower()
        
        # 🔧 FIX: Ya no hacemos `continue` si dice "Desconocido". Queremos que el partido aparezca sí o sí.
        es_cabecera = False
        for basura in palabras_basura:
            if basura in texto_unido:
                es_cabecera = True
                break
                
        if es_cabecera:
            continue
            
        goles_loc = leer_numero_aislado(roi_gol_loc)
        goles_vis = leer_numero_aislado(roi_gol_vis)
        
        goles_loc = goles_loc if goles_loc is not None else 0
        goles_vis = goles_vis if goles_vis is not None else 0
        
        pasa = equipo_local if goles_loc > goles_vis else (equipo_visitante if goles_vis > goles_loc else "Empate")
        
        partido = {
            "local": equipo_local,
            "visitante": equipo_visitante,
            "goles_local": goles_loc,
            "goles_visitante": goles_vis,
            "pasa": pasa
        }
        
        partidos_extraidos.append(partido)
        print(f"[{partido['local']}] {partido['goles_local']} - {partido['goles_visitante']} [{partido['visitante']}]")
        
    return partidos_extraidos

def procesar_fase_eliminatoria_completa(fase_origen):
    dir_participantes = ROOT_DIR / "participantes"
    if not dir_participantes.exists(): return
        
    participantes = [p for p in dir_participantes.iterdir() if p.is_dir()]
    if not participantes: return
        
    try:
        idx_inicio = FASES_ORDENADAS.index(fase_origen)
        fases_a_leer = FASES_ORDENADAS[idx_inicio:]
    except ValueError: return

    for p_folder in participantes:
        nombre_jugador = p_folder.name
        ruta_fase_origen = p_folder / "pronosticos" / "eliminatorias" / fase_origen
        
        if not ruta_fase_origen.exists(): continue
            
        print(f"\n⚡ Procesando cuadro completo de -> {nombre_jugador.upper()} ⚡")
        
        porra_completa = {
            "participante": nombre_jugador,
            "fase_origen": fase_origen,
            "predicciones": {}
        }
        
        archivos_leidos = 0
        for sub_fase in fases_a_leer:
            ruta_img = ruta_fase_origen / f"{sub_fase}.png"
            if ruta_img.exists():
                partidos = extraer_partidos_de_imagen(ruta_img)
                if partidos:
                    porra_completa["predicciones"][sub_fase] = partidos
                    archivos_leidos += 1
            else:
                print(f"   ⚠️ Falta la imagen {sub_fase}.png")
                
        if archivos_leidos > 0:
            ruta_json_salida = ruta_fase_origen / f"{fase_origen}.json"
            with open(ruta_json_salida, 'w', encoding='utf-8') as f:
                json.dump(porra_completa, f, ensure_ascii=False, indent=4)
            print(f"\n💾 Guardado Super-JSON en: {ruta_json_salida.relative_to(ROOT_DIR)}")

def menu_interactivo_ocr():
    print("\n" + "="*50)
    print(" 📸 MÓDULO OCR: PROCESAMIENTO MASIVO DE CAPTURAS")
    print("="*50)
    print("\nFases disponibles para procesar:")
    print(" - dieciseisavos\n - octavos\n - cuartos\n - semifinales\n - finales")
    
    fase_elegida = input("\n👉 Escribe la fase origen que quieres procesar: ").strip().lower()
    
    if fase_elegida not in FASES_ORDENADAS:
        print("\n❌ Error: Fase no reconocida. Asegúrate de escribirla correctamente.")
        return
        
    print(f"\n🚀 Iniciando lectura masiva para la carpeta: {fase_elegida.upper()}")
    procesar_fase_eliminatoria_completa(fase_elegida)

if __name__ == "__main__":
    menu_interactivo_ocr()