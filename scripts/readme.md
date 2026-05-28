# ⚙️ Documentación del Motor: Porra del Mundial 2026

Este documento detalla la arquitectura, el flujo de datos y el funcionamiento del ecosistema de scripts que dan vida a la Porra del Mundial. El sistema está diseñado para extraer, transformar, calcular y guardar información de forma autónoma.

---

## 🗄️ FASE 1: Las Fuentes de Datos (Extracción y Almacenamiento)

El sistema bebe de 4 fuentes distintas para crear los pronósticos de los jugadores y establecer la realidad oficial. Cada jugador dispone de una carpeta propia en `participantes/nombre_jugador/` para aislar sus datos.

*   **Script 00 - Generador de Calendario:** Genera el índice `config/jornadas.json` que divide inteligentemente los 72 partidos de grupos en **6 jornadas manejables de 12 partidos** (Bloques A-F y G-L), y empaqueta las eliminatorias.
*   **Script 01 - El Pronóstico Base (Infobae):**
    *   **Origen:** API oculta de la web de Infobae.
    *   **Función:** Crea la estructura de carpetas del jugador y descarga su predicción inicial completa (Fase de Grupos y Campeón).
    *   **Almacenamiento:** `participantes/nombre/pronosticos/grupos/nombre_base.json`.
*   **Script 02 - Las Eliminatorias en Vivo (OCR Livefutbol):**
    *   **Origen:** Capturas de pantalla de la web de Livefutbol.
    *   **Función:** Usa Visión Artificial (EasyOCR + Template Matching) para leer milimétricamente quién juega, cuántos goles marcan y quién pasa en cada ronda eliminatoria.
    *   **Almacenamiento:** `participantes/nombre/pronosticos/eliminatorias/fase/fase.json`.
*   **Script 03 - Los Premios Extra (Google Forms):**
    *   **Origen:** Archivo `.csv` exportado de Google Forms.
    *   **Función:** Lee las respuestas a preguntas subjetivas (MVP, Bota de Oro, Sorpresa...).
    *   **Almacenamiento:** `participantes/nombre/pronosticos/premios.json`.
*   **Script 05 - La Realidad Absoluta (SofaScore):**
    *   **Origen:** API oficial de SofaScore.
    *   **Función:** Rastrea los partidos jugados reales, los resultados exactos y quién se clasifica en la vida real.
    *   **Almacenamiento:** `data/resultados/realidad_oficial.json` *(La fuente de la verdad para puntuar)*.

---

## 🕹️ FASE 2: La Economía del Juego (Puntuaciones)

Todo el motor está gobernado por el archivo `config/settings.json`. Usando valores booleanos (`0` o `1`), las mecánicas se pueden activar o desactivar al vuelo. Los puntos se consiguen de **4 formas distintas**:

1.  **El Partido a Partido (Micro):**
    *   **Acierto 1X2:** +1 punto por acertar el ganador o empate.
    *   **Acierto Exacto:** +3 puntos por clavar los goles (condicionado a acertar el 1X2).
2.  **El Multiplicador de Racha (Fidelidad):**
    *   **Funcionamiento:** Exclusivo de eliminatorias. El multiplicador base es `x1.0`. Por cada fase anterior en la que el jugador confió en ese equipo, el multiplicador sube `+0.5`.
    *   **Propósito:** Obliga a decidir entre asegurar puntos conservadores o arriesgar manteniendo la lealtad a un equipo para multiplicar ganancias.
3.  **La Guerra de Jornadas (Macro):**
    *   **Funcionamiento:** En cada bloque de partidos (ej. los 12 partidos de J1.1), se evalúan los aciertos 1X2 puros. El que más acierta recibe **+2 puntos** (Ganador) y el que menos, **-2 puntos** (Perdedor).
    *   **Propósito:** Fomentar el componente competitivo directo (PvP). En caso de empate masivo, los bonos se anulan.
4.  **El Botín Final (Cierre):**
    *   **Grupos:** Puntos por adivinar quién clasifica y su posición exacta.
    *   **Podio:** Recompensas por acertar el Campeón, Subcampeón y Tercer puesto.
    *   **Forms:** Recompensas de alto valor por los premios subjetivos (Bota de Oro, Sorpresa, Mejor Gol, etc.).

---

## ⚙️ FASE 3: El Motor de Cálculo Dividido (Familia Script 06)

Para garantizar la mantenibilidad y evitar colapsos lógicos, el motor de cálculo se divide en 3 cerebros de ejecución secuencial:

*   **`06a_motor_partidos.py` (El Contable):** Evalúa partido a partido. Comprueba los goles, aplica la función recursiva de Racha leyendo el historial de pronósticos del jugador, asigna los puntos base y registra el conteo total de plenos y aciertos 1X2 de cada participante.
*   **`06b_motor_jornadas.py` (El Analista):** Consume los registros generados por el 06a, los cruza con el índice de jornadas y calcula quiénes se llevan los bonos de +2 (Ganador) y -2 (Perdedor) en cada bloque.
*   **`06c_motor_cierre.py` (El Juez Supremo):** Suma las puntuaciones de Grupos, los premios finales de Forms y el Podio. Finalmente, aplica un **sistema de desempates dinámico** (ej. 1º Puntos totales, 2º Más aciertos 1X2, 3º Más aciertos exactos, 4º Acertar el Campeón) para generar el `ranking_oficial.csv`.

---

## 📔 FASE 4: La Transparencia (El Libro de Cuentas)

Para asegurar la trazabilidad absoluta de las puntuaciones, a medida que los motores 06 ejecutan sus cálculos, redactan y actualizan un archivo llamado `historial_puntos.json` en el directorio `estadisticas/` de **cada jugador**.

Este archivo inmutable registra:
*   El desglose de cada partido: si se acertó, el multiplicador de racha aplicado y los puntos netos obtenidos.
*   El rendimiento por jornada: volumen de aciertos y aplicación de bonos (Ganador/Perdedor/Neutral).
*   La resolución final de los premios a largo plazo.
*   **La posición oficial final** en el ranking global del torneo tras aplicar desempates.