# core/renderer.py
import math
import pygame
import os


COLOR_FONDO          = (62,  135,  76)
COLOR_VIA            = (45,   45,  45)
COLOR_BORDE          = (92,   92,  92)
COLOR_LINEA_AMARILLA = (255, 204,   0)
COLOR_LINEA_BLANCA   = (245, 245, 245)
COLOR_PANEL          = (25,   25,  30)
COLOR_TEXTO          = (235, 235, 235)

_COLORES_SEMAFORO = {
    "ROJO":     (220,  40,  40),
    "AMARILLO": (255, 185,   0),
    "VERDE":    ( 40, 200,  80),
}
_APAGADO       = (70, 70, 70)
_SEM_GAP       = 8
_SEM_TEXTO_GAP = 7

_fuente_semaforo = None
_fuente_debug_s  = None
_panel_scroll     = 0
_panel_scroll_max = 0
_tiempo_total = 0.0

_LOGO_BASE = None
_RUTA_LOGO = os.path.join("assets", "ui", "citypulse_logo.png")

def _obtener_logo_base():
    global _LOGO_BASE
    if _LOGO_BASE is None:
        try:
            _LOGO_BASE = pygame.image.load(_RUTA_LOGO).convert_alpha()
        except Exception:
            _LOGO_BASE = None
    return _LOGO_BASE

def _dibujar_logo_marca_agua(pantalla, escenario):
    logo_base = _obtener_logo_base()
    if logo_base is None: return
    vias_h = [v for v in escenario.vias if v.orientacion == "horizontal"]
    vias_v = [v for v in escenario.vias if v.orientacion == "vertical"]
    for vh in vias_h:
        for vv in vias_v:
            if (vh.y < vv.y+vv.alto and vh.y+vh.alto > vv.y
                    and vv.x < vh.x+vh.ancho and vv.x+vv.ancho > vh.x):
                x1 = max(vh.x, vv.x); y1 = max(vh.y, vv.y)
                x2 = min(vh.x+vh.ancho, vv.x+vv.ancho)
                y2 = min(vh.y+vh.alto, vv.y+vv.alto)
                aw, ah = x2-x1, y2-y1
                if aw <= 0 or ah <= 0: continue
                lado = int(min(aw, ah) * 0.95)
                prop = logo_base.get_height() / logo_base.get_width()
                logo = pygame.transform.smoothscale(logo_base, (lado, max(1, int(lado*prop)))).convert_alpha()
                logo = logo.copy(); logo.set_alpha(100)
                pantalla.blit(logo, logo.get_rect(center=(x1+aw//2, y1+ah//2)))

def panel_scroll(delta: int):
    """Llamar desde main.py al recibir MOUSEWHEEL sobre el panel."""
    global _panel_scroll, _panel_scroll_max
    _panel_scroll = max(0, min(_panel_scroll_max, _panel_scroll - delta * 18))

def _get_fuente_semaforo():
    global _fuente_semaforo
    if _fuente_semaforo is None:
        _fuente_semaforo = pygame.font.SysFont("consolas", 16, bold=True)
    return _fuente_semaforo


def _get_fuente_debug():
    global _fuente_debug_s
    if _fuente_debug_s is None:
        _fuente_debug_s = pygame.font.SysFont("consolas", 9)
    return _fuente_debug_s

def _intervalos_cruce(via, escenario, margen=0):
    bloqueos = []
    if via.orientacion == "horizontal":
        pares = [lp for lp in escenario.lineas_pare
                 if lp.alto > lp.ancho and (via.y < lp.y + lp.alto and via.y + via.alto > lp.y)]
        pares.sort(key=lambda lp: lp.x)
        i = 0
        while i < len(pares) - 1:
            izq = pares[i]
            der = pares[i + 1]
            # si están cerca (mismo cruce), los agrupa
            if der.x - (izq.x + izq.ancho) < 200:
                bloqueos.append((izq.x - margen, der.x + der.ancho + margen))
                i += 2
            else:
                i += 1
    else:
        pares = [lp for lp in escenario.lineas_pare
                 if lp.ancho > lp.alto and (via.x < lp.x + lp.ancho and via.x + via.ancho > lp.x)]
        pares.sort(key=lambda lp: lp.y)
        i = 0
        while i < len(pares) - 1:
            sup = pares[i]
            inf = pares[i + 1]
            if inf.y - (sup.y + sup.alto) < 200:
                bloqueos.append((sup.y - margen, inf.y + inf.alto + margen))
                i += 2
            else:
                i += 1
    return bloqueos
def _dibujar_segmentos_linea(pantalla, color, via, pos_fija, bloqueos,
                              punteada=False, ancho=2, largo=12, espacio=8):
    def _punteada(inicio, fin):
        x1, y1 = inicio; x2, y2 = fin
        dx, dy = x2-x1, y2-y1
        dist = math.hypot(dx, dy)
        if dist == 0: return
        dx /= dist; dy /= dist
        dibujar = True; avance = 0
        while avance < dist:
            if dibujar:
                fs = min(avance + largo, dist)
                pygame.draw.line(pantalla, color,
                    (x1+dx*avance, y1+dy*avance), (x1+dx*fs, y1+dy*fs), ancho)
            avance += largo if dibujar else espacio
            dibujar = not dibujar

    if via.orientacion == "horizontal":
        cursor = via.x
        fin = via.x + via.ancho
        for a, b in bloqueos:
            if a > cursor:
                if punteada: _punteada((cursor, pos_fija), (a, pos_fija))
                else: pygame.draw.line(pantalla, color, (cursor, pos_fija), (a, pos_fija), ancho)
            cursor = max(cursor, b)
        if cursor < fin:
            if punteada: _punteada((cursor, pos_fija), (fin, pos_fija))
            else: pygame.draw.line(pantalla, color, (cursor, pos_fija), (fin, pos_fija), ancho)
    else:
        cursor = via.y
        fin = via.y + via.alto
        for a, b in bloqueos:
            if a > cursor:
                if punteada: _punteada((pos_fija, cursor), (pos_fija, a))
                else: pygame.draw.line(pantalla, color, (pos_fija, cursor), (pos_fija, a), ancho)
            cursor = max(cursor, b)
        if cursor < fin:
            if punteada: _punteada((pos_fija, cursor), (pos_fija, fin))
            else: pygame.draw.line(pantalla, color, (pos_fija, cursor), (pos_fija, fin), ancho)

def _dibujar_via(pantalla: pygame.Surface, via, escenario) -> None:
    rect = pygame.Rect(via.x, via.y, via.ancho, via.alto)
    pygame.draw.rect(pantalla, COLOR_VIA, rect)
    pygame.draw.rect(pantalla, COLOR_BORDE, rect, 2)
    bloqueos = _intervalos_cruce(via, escenario, margen=0)
    if via.linea_central:
        if via.orientacion == "horizontal":
            _dibujar_segmentos_linea(pantalla, COLOR_LINEA_AMARILLA, via,
                                     via.y + via.alto // 2, bloqueos, punteada=False, ancho=3)
        else:
            _dibujar_segmentos_linea(pantalla, COLOR_LINEA_AMARILLA, via,
                                     via.x + via.ancho // 2, bloqueos, punteada=False, ancho=3)
    for linea in via.lineas_separacion:
        if linea["orientacion"] == "horizontal" and via.orientacion == "horizontal":
            _dibujar_segmentos_linea(pantalla, COLOR_LINEA_BLANCA, via,
                                     linea["pos"], bloqueos, punteada=True, ancho=2)
        elif linea["orientacion"] == "vertical" and via.orientacion == "vertical":
            _dibujar_segmentos_linea(pantalla, COLOR_LINEA_BLANCA, via,
                                     linea["pos"], bloqueos, punteada=True, ancho=2)
def _dibujar_cebra(pantalla: pygame.Surface, cebra) -> None:
    base = min(cebra.ancho, cebra.alto)
    franja = max(4, int(base * 0.08))
    espacio = max(4, int(base * 0.06))
    if cebra.ancho >= cebra.alto:
        xx = cebra.x
        while xx < cebra.x + cebra.ancho:
            pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA, (xx, cebra.y, franja, cebra.alto))
            xx += franja + espacio
    else:
        yy = cebra.y
        while yy < cebra.y + cebra.alto:
            pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA, (cebra.x, yy, cebra.ancho, franja))
            yy += franja + espacio

def _dibujar_linea_pare(pantalla, lp):
    pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA,
                     pygame.Rect(lp.x, lp.y, lp.ancho, lp.alto))


def _dibujar_semaforo(pantalla, semaforo, estado, restante):
    fuente = _get_fuente_semaforo()
    es_h   = semaforo.grupo.startswith("H")
    ancho_caja, alto_caja = (64, 24) if es_h else (24, 64)

    lados = {
        "izquierda": pygame.Rect(semaforo.x - ancho_caja - _SEM_GAP,
                                 semaforo.y - alto_caja // 2,
                                 ancho_caja, alto_caja),
        "derecha":   pygame.Rect(semaforo.x + _SEM_GAP,
                                 semaforo.y - alto_caja // 2,
                                 ancho_caja, alto_caja),
        "arriba":    pygame.Rect(semaforo.x - ancho_caja // 2,
                                 semaforo.y - alto_caja - _SEM_GAP,
                                 ancho_caja, alto_caja),
        "abajo":     pygame.Rect(semaforo.x - ancho_caja // 2,
                                 semaforo.y + _SEM_GAP,
                                 ancho_caja, alto_caja),
    }
    cuerpo = lados.get(
        semaforo.lado,
        pygame.Rect(semaforo.x - ancho_caja // 2,
                    semaforo.y - alto_caja // 2,
                    ancho_caja, alto_caja),
    )

    pygame.draw.rect(pantalla, (30, 30, 30), cuerpo, border_radius=5)
    pygame.draw.rect(pantalla, (10, 10, 10), cuerpo, 2, border_radius=5)

    if es_h:
        luces = [
            ("ROJO",     cuerpo.x + 12,              cuerpo.centery),
            ("AMARILLO", cuerpo.x + ancho_caja // 2, cuerpo.centery),
            ("VERDE",    cuerpo.x + ancho_caja - 12, cuerpo.centery),
        ]
    else:
        luces = [
            ("ROJO",     cuerpo.centerx, cuerpo.y + 12),
            ("AMARILLO", cuerpo.centerx, cuerpo.y + alto_caja // 2),
            ("VERDE",    cuerpo.centerx, cuerpo.y + alto_caja - 12),
        ]

    # ── glow del estado activo (una sola vez, fuera del loop) ──────────────
    color_activo     = _COLORES_SEMAFORO[estado]
    cx_glow, cy_glow = next((lx, ly) for n, lx, ly in luces if n == estado)
    glow = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color_activo, 60), (20, 20), 18)
    pygame.draw.circle(glow, (*color_activo, 35), (20, 20), 13)
    pantalla.blit(glow, (cx_glow - 20, cy_glow - 20))
    # ── fin glow ───────────────────────────────────────────────────────────

    # ── círculos de luces ──────────────────────────────────────────────────
    for nombre, lx, ly in luces:
        color = _COLORES_SEMAFORO[nombre] if nombre == estado else _APAGADO
        pygame.draw.circle(pantalla, color, (lx, ly), 8)
        borde = (180, 180, 180) if nombre == estado else (55, 55, 55)
        pygame.draw.circle(pantalla, borde, (lx, ly), 8, 2)
    # ── fin círculos ───────────────────────────────────────────────────────

    txt      = fuente.render(str(max(0, int(restante + 0.999))), True, COLOR_TEXTO)
    txt_rect = txt.get_rect()
    if es_h:
        if semaforo.lado in ("arriba", "izquierda"):
            txt_rect.midbottom = (cuerpo.centerx, cuerpo.top  - _SEM_TEXTO_GAP)
        else:
            txt_rect.midtop    = (cuerpo.centerx, cuerpo.bottom + _SEM_TEXTO_GAP)
    else:
        if semaforo.lado in ("izquierda", "arriba"):
            txt_rect.midright  = (cuerpo.left  - _SEM_TEXTO_GAP, cuerpo.centery)
        else:
            txt_rect.midleft   = (cuerpo.right + _SEM_TEXTO_GAP, cuerpo.centery)
    pantalla.blit(txt, txt_rect)

def _render_vehiculo_surface(v, carril):
    """
    Devuelve (surface, rect) con rotación visual aplicada SOLO para render.
    No modifica ningún atributo lógico del vehículo.

    La rotación se calcula a partir de v.angulo_visual (grados).
    Para carriles verticales (eje=="y") se invierte el signo porque
    el sprite ya está rotado 90° por _cargar_imagen y la inclinación
    debe ir en el eje perpendicular correcto.

    El rect resultante siempre mantiene el mismo centro visual (x, y)
    calculado con posicion_px() + offset, de modo que el bounding box
    crece simétricamente y nunca desplaza el centro.
    """
    ancho_px = v.ancho if carril.eje == "x" else v.alto
    alto_px  = v.alto  if carril.eje == "x" else v.ancho

    angulo = getattr(v, "angulo_visual", 0.0)

    if hasattr(v, "image") and v.image is not None:
        base_surf = v.image
    else:
        base_surf = pygame.Surface((ancho_px, alto_px), pygame.SRCALPHA)
        base_surf.fill(v.color)
        pygame.draw.rect(base_surf, (20, 20, 20),
                         base_surf.get_rect(), 1, border_radius=4)

    if abs(angulo) < 0.3:
        # Sin rotación apreciable — blit directo, sin coste de rotate
        surf = base_surf
    else:
        surf = pygame.transform.rotate(base_surf, -angulo)   # pygame: CCW positivo

    return surf


def dibujar_escenario(pantalla: pygame.Surface, escenario) -> None:
    pantalla.fill(COLOR_FONDO)
    for via in escenario.vias:
        _dibujar_via(pantalla, via, escenario)   # ← pasa escenario
    _dibujar_logo_marca_agua(pantalla, escenario) # ← nuevo
    for cebra in escenario.cebras:
        _dibujar_cebra(pantalla, cebra)
    for lp in escenario.lineas_pare:
        _dibujar_linea_pare(pantalla, lp)
    for semaforo in escenario.semaforos:
        estado = escenario.controlador.estado_grupo(semaforo.grupo)
        restante = escenario.controlador.tiempo_restante_grupo(semaforo.grupo)
        _dibujar_semaforo(pantalla, semaforo, estado, restante)

    def _get_logo_font():
        global _logo_font
        if _logo_font is None:
            _logo_font = pygame.font.SysFont("consolas", 18, bold=True)
        return _logo_font


    def _dibujar_logo_interseccion(pantalla: pygame.Surface, escenario) -> None:
        fuente = _get_logo_font()
        vias_h = [v for v in escenario.vias if v.orientacion == "horizontal"]
        vias_v = [v for v in escenario.vias if v.orientacion == "vertical"]
        intersecciones = set()
        for vh in vias_h:
            for vv in vias_v:
                cx = vv.x + vv.ancho // 2
                cy = vh.y + vh.alto // 2
                intersecciones.add((cx, cy))
        for cx, cy in intersecciones:
            # fondo oscuro semitransparente
            s = pygame.Surface((110, 22), pygame.SRCALPHA)
            s.fill((0, 0, 0, 120))
            pantalla.blit(s, (cx - 55, cy - 11))
            # texto: "City" blanco + "Pulse" cian
            t1 = fuente.render("City", True, (255, 255, 255))
            t2 = fuente.render("Pulse", True, (0, 210, 220))
            pantalla.blit(t1, (cx - 52, cy - 10))
            pantalla.blit(t2, (cx - 52 + t1.get_width(), cy - 10))
            _dibujar_logo_interseccion(pantalla, escenario)


def dibujar_vehiculos(pantalla, escenario, gestor_eventos=None):
    global _tiempo_total
    _tiempo_total += 0.016

    wobble = 0.0
    if gestor_eventos is not None:
        wobble = gestor_eventos.wobble_lluvia(_tiempo_total)

    for carril in escenario.carriles:
        for v in carril.vehiculos:
            x, y = v.posicion_px()

            offset_cambio   = int(getattr(v, "offset_lateral",  0.0))
            ancho_px_carril = getattr(carril, "ancho_carril_px", 0)
            pos_lat         = getattr(v, "posicion_lateral",    0.0)
            offset_posicion = int(pos_lat * ancho_px_carril / 2)
            offset_total    = offset_cambio + offset_posicion

            if carril.eje == "x":
                y += offset_total
            else:
                x += offset_total

            # wobble visual lluvia — no toca posición real
            if wobble != 0.0:
                seed = x * 0.05 if carril.eje == "x" else y * 0.05
                w_offset = int(wobble * math.sin(_tiempo_total * 2.1 + seed))
                if carril.eje == "x":
                    y += w_offset
                else:
                    x += w_offset

            surf = _render_vehiculo_surface(v, carril)
            rect = surf.get_rect(center=(x, y))

            shadow_w = max(10, int(rect.width * 0.75))
            shadow_h = max(6,  int(rect.height * 0.45))
            shadow   = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 55), (0, 0, shadow_w, shadow_h))
            pantalla.blit(shadow, (rect.centerx - shadow_w // 2 + 3,
                                   rect.centery - shadow_h // 2 + 5))

            pantalla.blit(surf, rect)

            # luces intermitentes prioritarios
            if getattr(v, "ES_PRIORITARIO", False):
                t = pygame.time.get_ticks()
                ciclo = (t // 300) % 2
                col_a = (255, 30, 30) if ciclo == 0 else (30, 30, 255)
                col_b = (30, 30, 255) if ciclo == 0 else (255, 30, 30)
                tam = max(4, min(7, rect.width // 6))
                cx, cy = rect.centerx, rect.centery

                # aura pulsante
                pulso = abs(math.sin(t / 300.0))
                radio_aura = int(rect.width * 0.65 + pulso * 12)
                alpha_aura = int(40 + pulso * 50)
                col_aura = col_a
                aura_surf = pygame.Surface((radio_aura * 2, radio_aura * 2), pygame.SRCALPHA)
                pygame.draw.circle(aura_surf, (*col_aura, alpha_aura),
                                   (radio_aura, radio_aura), radio_aura)
                pantalla.blit(aura_surf, (cx - radio_aura, cy - radio_aura))

                # luces originales
                pygame.draw.rect(pantalla, col_a, (cx - tam - 2, cy - tam // 2, tam, tam))
                pygame.draw.rect(pantalla, col_b, (cx + 2, cy - tam // 2, tam, tam))

def dibujar_debug_overlay(pantalla, escenario, gestor):
    try:
        from core.simulacion import (
            DEBUG_ACTIVO, DEBUG_OVERLAY,
            debug_errores_frame, debug_historial,
            debug_perf, debug_contadores,
            _d_tiempos_estado,
        )
    except ImportError:
        return

    if not DEBUG_ACTIVO or not DEBUG_OVERLAY:
        return

    fuente = _get_fuente_debug()

    errores_ids = set()
    for err in debug_errores_frame():
        partes = err.split(" ")
        if len(partes) > 1:
            errores_ids.add(partes[1])

    # ── etiquetas por vehículo ─────────────────────────────────────────────
    for carril in escenario.carriles:
        for v in carril.vehiculos:
            x, y = v.posicion_px()
            offset_cambio   = int(getattr(v, "offset_lateral",  0.0))
            ancho_px_carril = getattr(carril, "ancho_carril_px", 0)
            pos_lat         = getattr(v, "posicion_lateral",    0.0)
            offset_posicion = int(pos_lat * ancho_px_carril / 2)
            offset_total    = offset_cambio + offset_posicion
            if carril.eje == "x":
                y += offset_total
            else:
                x += offset_total

            estado = getattr(v, "_estado_cambio", "?")

            if v.id in errores_ids:
                color_borde = (220, 50, 50)
            else:
                color_borde = {
                    "LIBRE":      (70,  70,  70),
                    "PREPARANDO": (240, 190,  30),
                    "CAMBIANDO":  ( 30, 190, 240),
                }.get(estado, (220, 50, 50))

            ancho_px    = v.ancho if carril.eje == "x" else v.alto
            alto_px     = v.alto  if carril.eje == "x" else v.ancho
            rect_logico = pygame.Rect(0, 0, ancho_px, alto_px)
            rect_logico.center = (x, y)
            pygame.draw.rect(pantalla, color_borde, rect_logico, 1)

            # label compacto: id + estado + vel + offset si activo
            off_val = getattr(v, "offset_lateral", 0.0)
            label   = f"{v.id[-4:]} {estado[0]}  {v.velocidad_actual:.0f}"
            if abs(off_val) > 0.5:
                label += f"  {off_val:+.0f}px"

            surf_label = fuente.render(label, True, color_borde)
            lw, lh     = surf_label.get_size()
            lx         = rect_logico.left
            ly         = rect_logico.top - lh - 2
            # fondo semitransparente del label
            bg = pygame.Surface((lw + 4, lh + 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 130))
            pantalla.blit(bg,         (lx - 2, ly - 1))
            pantalla.blit(surf_label, (lx,     ly))

    # ── historial de errores (esquina inferior izquierda) ──────────────────
    errores = debug_historial(6)
    if errores:
        py = pantalla.get_height() - 14 * len(errores) - 10
        for err in errores:
            es_critico = any(
                t in err for t in
                ("DOBLE", "OVERLAP", "NAN", "INV", "OWNERSHIP", "ZOMBIE")
            )
            color = (220, 60, 60) if es_critico else (230, 185, 40)
            surf  = fuente.render(err[:68], True, color)
            bg    = pygame.Surface((surf.get_width() + 6, surf.get_height() + 2),
                                   pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            pantalla.blit(bg,   (6,  py - 1))
            pantalla.blit(surf, (9,  py))
            py += 14

    # ── panel de rendimiento (esquina superior derecha) ────────────────────
    perf  = debug_perf()
    cont  = debug_contadores()
    frame = getattr(gestor, "_frame_n", 0)

    lineas_perf = [
        ("frame",    f"#{frame}",                           (160, 165, 180)),
        ("spawn",    f"{perf.get('spawn', 0):.1f}ms",       (140, 200, 140)),
        ("física",   f"{perf.get('fisica', 0):.1f}ms",      (140, 200, 140)),
        ("lc",       f"{perf.get('lane_change_intent',0):.1f}ms", (140, 200, 140)),
        ("activos",  f"{cont.get('vehiculos_en_listas', 0)}", (200, 200, 140)),
        ("errores",  f"{cont.get('frames_con_error', 0)}",
         (220, 60, 60) if cont.get("frames_con_error", 0) > 0 else (140, 200, 140)),
    ]

    col_key = 50
    col_val = 94
    fila_h  = 14
    panel_w = col_key + col_val + 12
    panel_h = len(lineas_perf) * fila_h + 10
    px_r    = pantalla.get_width() - panel_w - 6
    py_r    = 6

    bg_perf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg_perf.fill((0, 0, 0, 150))
    pantalla.blit(bg_perf, (px_r, py_r))
    pygame.draw.rect(pantalla, (55, 58, 70),
                     pygame.Rect(px_r, py_r, panel_w, panel_h), 1)

    fy = py_r + 5
    for clave, valor, color in lineas_perf:
        s_k = fuente.render(clave, True, (100, 105, 120))
        s_v = fuente.render(valor, True, color)
        pantalla.blit(s_k, (px_r + 6,           fy))
        pantalla.blit(s_v, (px_r + 6 + col_key, fy))
        fy += fila_h


def dibujar_panel(pantalla, gestor, x, ancho, alto, fuente_titulo, fuente_texto, debug_activo=False):
    global _panel_scroll, _panel_scroll_max

    # ── fondo fijo ─────────────────────────────────────────────────────────
    pygame.draw.rect(pantalla, (22, 24, 30), pygame.Rect(x, 0, ancho, alto))
    pygame.draw.line(pantalla, (55, 58, 70), (x, 0), (x, alto), 2)

    m    = gestor.metricas
    esc  = gestor.escenario
    ctrl = esc.controlador

    dbg_on = debug_activo
    try:
        from core.simulacion import debug_contadores
        err_total = debug_contadores().get("frames_con_error", 0)
    except ImportError:
        err_total = 0

    # ── surface de contenido (scroll) ──────────────────────────────────────
    CONTENT_H = 2000
    content   = pygame.Surface((ancho, CONTENT_H))
    content.fill((22, 24, 30))

    cpx = 12    # padding horizontal
    cpy = 8     # cursor vertical

    def _sep():
        nonlocal cpy
        pygame.draw.line(content, (40, 43, 52),
                         (6, cpy), (ancho - 6, cpy), 1)
        cpy += 6

    def _sec(texto):
        nonlocal cpy
        s = fuente_texto.render(texto.upper(), True, (85, 90, 112))
        content.blit(s, (cpx, cpy))
        cpy += s.get_height() + 3

    def _lin(texto, color=COLOR_TEXTO):
        nonlocal cpy
        s = fuente_texto.render(texto, True, color)
        content.blit(s, (cpx, cpy))
        cpy += s.get_height() + 3

    def _barra(label, valor):
        nonlocal cpy
        bw = ancho - 24
        s  = fuente_texto.render(label, True, (120, 125, 145))
        content.blit(s, (cpx, cpy))
        cpy += s.get_height() + 2
        pygame.draw.rect(content, (36, 39, 48),
                         pygame.Rect(cpx, cpy, bw, 5), border_radius=2)
        fill = max(0.0, min(1.0, valor))
        if fill > 0:
            fc = ((55, 195, 95)  if fill < 0.45 else
                  (225, 180, 35) if fill < 0.70 else
                  (205, 55, 55))
            pygame.draw.rect(content, fc,
                             pygame.Rect(cpx, cpy, int(bw * fill), 5),
                             border_radius=2)
        cpy += 5 + 6

    # ── título ─────────────────────────────────────────────────────────────
    s_t = fuente_titulo.render("CityPulse", True, (222, 225, 235))
    content.blit(s_t, (cpx, cpy))
    cpy += s_t.get_height() + 1
    s_s = fuente_texto.render(esc.nombre[:24], True, (75, 80, 100))
    content.blit(s_s, (cpx, cpy))
    cpy += s_s.get_height() + 7
    _sep()

    # ── estado ─────────────────────────────────────────────────────────────
    _sec("Estado")
    ec = (70, 190, 110) if not gestor.pausado else (210, 170, 40)
    _lin(f"{'▶ Corriendo' if not gestor.pausado else '⏸ Pausado'}", ec)
    _lin(f"Velocidad  {gestor.escala_tiempo:.2f}×")
    _sep()

    # ── tráfico ────────────────────────────────────────────────────────────
    _sec("Tráfico")
    _lin(f"Activos    {m['activos']}")
    _lin(f"Generados  {m['generados']}")
    _lin(f"Salidos    {m['salidos']}")
    _lin(f"Vel prom   {m['velocidad_promedio']:.1f} px/s")
    _lin(f"Cola       {m['cola_total']}")
    _lin(f"Espera     {m['tiempo_espera_promedio']:.1f}s")
    if m["prioritarios_activos"] > 0:
        _lin(f"Priorit    {m['prioritarios_activos']}  "
             f"bloq {m['prioritarios_bloqueados']}",
             (245, 190, 50))
    _sep()

    # ── semáforos ──────────────────────────────────────────────────────────
    _sec("Semáforos")
    for grupo, nombre_g in (("H", "Horizontal"), ("V", "Vertical")):
        est  = ctrl.estado_grupo(grupo)
        rest = ctrl.tiempo_restante_grupo(grupo)
        col  = {"VERDE":    (50, 190, 80),
                "AMARILLO": (220, 175, 30),
                "ROJO":     (200, 50,  50)}.get(est, COLOR_TEXTO)
        _lin(f"{nombre_g}  {est}  {rest:.1f}s", col)
    _sep()

    # ── congestión ─────────────────────────────────────────────────────────
    _sec("Congestión carriles")
    for carril in esc.carriles:
        _barra(carril.id_carril[:18], carril.nivel_congestion())
    _sep()

    sugerencias = m.get("sugerencias_congestion", [])
    if sugerencias:
        _sep()
        _sec("Optimización sugerida")
        for sg in sugerencias[:3]:
            col = (205, 55, 55) if sg["prioridad"] == "ALTA" else (225, 180, 35)
            _lin(f"{sg['carril']} ({int(sg['nivel'] * 100)}%)", col)
            _lin(f"→ {sg['accion']}", (160, 165, 185))
    # ── eventos activos ────────────────────────────────────────────────────
    try:
        estado_eventos = gestor.gestor_eventos.estado()
        _sec("Eventos")

        etiquetas_ev = {
            "hora_pico": ("⚡ Hora pico",  (245, 190,  50)),
            "lluvia":    ("🌧  Lluvia",    (130, 180, 230)),
            "niebla":    ("🌫  Niebla",    (190, 200, 190)),
            "accidente": ("🚨 Accidente",  (255,  80,  80)),
            "noche":     ("🌙 Noche",      ( 80, 100, 200)),
            "fiesta": ("🎉 Fiesta", (255, 80, 180)),
        }
        alguno = False
        for nombre, activo in estado_eventos.items():
            texto, col_ev = etiquetas_ev.get(nombre, (nombre, COLOR_TEXTO))
            col_final = col_ev if activo else (70, 72, 85)
            estado_txt = "ON " if activo else "OFF"
            _lin(f"{texto:<14} {estado_txt}", col_final)
            alguno = True
        if alguno:
            _sep()
    except AttributeError:
        pass
    # ── fin eventos ────────────────────────────────────────────────────────

    # ── debug ──────────────────────────────────────────────────────────────
    _lin(f"Debug visual  {'ON' if dbg_on else 'OFF'}",
         (70, 190, 110) if dbg_on else (90, 90, 105))
    err_col = (200, 50, 50) if err_total > 0 else (70, 190, 110)
    _lin(f"Err frames  {err_total}", err_col)
    _sep()

    # ── controles (solo los reales) ────────────────────────────────────────
    _sec("Controles")
    controles = [
        ("1 / 2 / 3", "cambiar escenario"),
        ("SPACE",     "pausar / reanudar"),
        ("+ / -",     "velocidad"),
        ("R",         "recargar escenario"),
        ("f1",         "Debug Mode"),
        ("T",  "hora pico"),
        ("Y",  "lluvia"),
        ("U",  "accidente"),
        ("I",  "niebla"),
        ("O",  "noche"),
        ("F", "fiesta mode"),
        ("ESC",       "salir"),
    ]
    for tecla, accion in controles:
        s_t = fuente_texto.render(tecla,  True, (160, 165, 185))
        s_a = fuente_texto.render(accion, True, (75, 80, 100))
        content.blit(s_t, (cpx,      cpy))
        content.blit(s_a, (cpx + 72, cpy))
        cpy += s_t.get_height() + 4

    cpy += 12  # margen inferior

    # ── scroll: calcular máximo y hacer blit recortado ────────────────────
    _panel_scroll_max = max(0, cpy - alto)
    _panel_scroll     = min(_panel_scroll, _panel_scroll_max)

    # clip para que nada dibuje fuera del panel
    pantalla.set_clip(pygame.Rect(x, 0, ancho, alto))
    pantalla.blit(content, (x, -_panel_scroll))
    pantalla.set_clip(None)

    # borde izquierdo fijo (encima del contenido)
    pygame.draw.line(pantalla, (55, 58, 70), (x, 0), (x, alto), 2)

    # ── indicador de scroll (si hay contenido oculto) ─────────────────────
    if _panel_scroll_max > 0:
        track_h    = alto - 16
        thumb_h    = max(24, int(track_h * alto / cpy))
        thumb_y    = 8 + int((track_h - thumb_h) * _panel_scroll / _panel_scroll_max)
        pygame.draw.rect(pantalla, (45, 48, 58),
                         pygame.Rect(x + ancho - 6, 8, 4, track_h),
                         border_radius=2)
        pygame.draw.rect(pantalla, (90, 95, 115),
                         pygame.Rect(x + ancho - 6, thumb_y, 4, thumb_h),
                         border_radius=2)

# ── overlays de eventos ────────────────────────────────────────────────────
import math as _math
import pygame as _pg

def _overlay_lluvia(pantalla, lluvia, ancho_sim, alto):
    if not lluvia.activo: return
    charco_surf = _pg.Surface((ancho_sim, alto), _pg.SRCALPHA)
    for ch in lluvia._charcos:
        x, y, rx, ry, vida, vida_max = ch
        alpha = int(70 * min(1.0, vida / vida_max))
        _pg.draw.ellipse(charco_surf, (60, 100, 140, alpha),
                         _pg.Rect(x - rx, y - ry, rx * 2, ry * 2))
        _pg.draw.ellipse(charco_surf, (120, 170, 210, alpha // 3),
                         _pg.Rect(x - rx//2, y - ry//2, rx, ry))
    pantalla.blit(charco_surf, (0, 0))
    velo = _pg.Surface((ancho_sim, alto), _pg.SRCALPHA)
    velo.fill((20, 35, 55, 38))
    pantalla.blit(velo, (0, 0))
    gota_surf = _pg.Surface((ancho_sim, alto), _pg.SRCALPHA)
    for g in lluvia._gotas:
        x, y, largo, _ = g
        x2 = int(x - largo * 0.18)
        if 0 <= int(x) <= ancho_sim:
            _pg.draw.line(gota_surf, (174, 214, 241, 90),
                          (int(x), int(y)), (x2, int(y + largo)), 1)
    pantalla.blit(gota_surf, (0, 0))


def _overlay_niebla(pantalla, niebla, ancho_sim, alto):
    alpha_int = int(niebla.alpha())
    if alpha_int <= 0: return
    surf = _pg.Surface((ancho_sim, alto), _pg.SRCALPHA)
    surf.fill((210, 215, 200, alpha_int))
    pantalla.blit(surf, (0, 0))
    t = _pg.time.get_ticks() / 4000.0
    for i in range(5):
        cx = int(ancho_sim * (0.15 + i * 0.18 + _math.sin(t + i) * 0.06))
        cy = int(alto      * (0.3  + i * 0.08 + _math.cos(t + i * 1.3) * 0.08))
        r  = int(160 + i * 30)
        parche = _pg.Surface((r * 2, r * 2), _pg.SRCALPHA)
        _pg.draw.circle(parche, (220, 225, 210, alpha_int // 3), (r, r), r)
        pantalla.blit(parche, (cx - r, cy - r))


def _overlay_accidente(pantalla, accidente, ancho_sim, alto):
    if not accidente.activo: return
    carril, pos = accidente.pos_accidente()
    if carril is None: return
    px, py = carril.posicion_mundo(pos)
    if not (0 <= px <= ancho_sim and 0 <= py <= alto): return
    s = _pg.Surface((44, 44), _pg.SRCALPHA)
    _pg.draw.polygon(s, (255, 200, 0, 220), [(22, 2), (42, 40), (2, 40)])
    _pg.draw.polygon(s, (180, 120, 0, 255), [(22, 2), (42, 40), (2, 40)], 2)
    fuente = _pg.font.SysFont("consolas", 20, bold=True)
    txt    = fuente.render("!", True, (40, 20, 0))
    s.blit(txt, (18, 12))
    pantalla.blit(s, (px - 22, py - 22))


def _overlay_noche(pantalla, noche, ancho_sim, alto):
    alpha_int = int(noche.alpha())
    if alpha_int <= 0: return
    surf = _pg.Surface((ancho_sim, alto), _pg.SRCALPHA)
    surf.fill((10, 12, 30, alpha_int))
    pantalla.blit(surf, (0, 0))


def _overlay_fiesta(pantalla, fiesta, ancho_sim, alto):
    if not fiesta.activo: return
    t    = _pg.time.get_ticks() / 1000.0
    surf = _pg.Surface((ancho_sim, alto), _pg.SRCALPHA)
    for i, col in enumerate(fiesta._COLORES):
        fase  = t * 1.2 + i * (_math.pi * 2 / len(fiesta._COLORES))
        cx    = int(ancho_sim * 0.5 + _math.cos(fase) * ancho_sim * 0.35)
        cy    = int(alto      * 0.5 + _math.sin(fase) * alto      * 0.35)
        radio = int(80 + 40 * _math.sin(t * 3 + i))
        alpha = int(35 + 20 * _math.sin(t * 2 + i))
        _pg.draw.circle(surf, (*col, alpha), (cx, cy), radio)
    pantalla.blit(surf, (0, 0))
    if not hasattr(_overlay_fiesta, "_fuente"):
        _overlay_fiesta._fuente = _pg.font.SysFont("consolas", 48, bold=True)
    col_txt  = fiesta._COLORES[int(t * 3) % len(fiesta._COLORES)]
    txt_surf = _overlay_fiesta._fuente.render("FIESTA MODE", True, col_txt)
    txt_surf.set_alpha(int(180 + 75 * _math.sin(t * 4)))
    pantalla.blit(txt_surf, (ancho_sim // 2 - txt_surf.get_width() // 2, 18))


def _dibujar_faros(pantalla, noche, escenario, ancho_sim, alto):
    intensidad = min(1.0, noche.alpha() / noche.ALPHA_MAX)
    if intensidad <= 0: return
    for carril in escenario.carriles:
        for v in carril.vehiculos:
            px, py = v.posicion_px()
            if not (0 <= px <= ancho_sim and 0 <= py <= alto): continue
            largo   = v.ancho
            ancho_v = v.alto
            es_moto = v.__class__.__name__ == "Moto"
            if carril.eje == "x":
                frente_x = px + carril.direccion * (largo // 2)
                faros = [(frente_x, py)] if es_moto else [
                    (frente_x, py - ancho_v // 4),
                    (frente_x, py + ancho_v // 4),
                ]
            else:
                frente_y = py + carril.direccion * (largo // 2)
                faros = [(px, frente_y)] if es_moto else [
                    (px - ancho_v // 4, frente_y),
                    (px + ancho_v // 4, frente_y),
                ]
            for fx, fy in faros:
                for r, a in [(28, 30), (18, 55), (9, 90)]:
                    faro_surf = _pg.Surface((r * 2, r * 2), _pg.SRCALPHA)
                    if carril.eje == "x":
                        ex = r if carril.direccion > 0 else 0
                        rect_elipse = _pg.Rect(ex, r // 2, r, r)
                    else:
                        ey = r if carril.direccion > 0 else 0
                        rect_elipse = _pg.Rect(r // 2, ey, r, r)
                    _pg.draw.ellipse(faro_surf,
                                     (255, 255, 180, int(a * intensidad)),
                                     rect_elipse)
                    pantalla.blit(faro_surf, (fx - r, fy - r))
                _pg.draw.circle(pantalla,
                                (255, 255, 220, int(160 * intensidad)),
                                (int(fx), int(fy)), 3)


def dibujar_eventos(pantalla, gestor_eventos, ancho_sim, alto, escenario=None):
    _overlay_lluvia  (pantalla, gestor_eventos.lluvia,    ancho_sim, alto)
    _overlay_niebla  (pantalla, gestor_eventos.niebla,    ancho_sim, alto)
    _overlay_noche   (pantalla, gestor_eventos.noche,     ancho_sim, alto)
    _overlay_accidente(pantalla, gestor_eventos.accidente, ancho_sim, alto)
    _overlay_fiesta  (pantalla, gestor_eventos.fiesta,    ancho_sim, alto)
    if escenario is not None:
        _dibujar_faros(pantalla, gestor_eventos.noche, escenario, ancho_sim, alto)


def dibujar_nombre_eventos(pantalla, gestor_eventos, fuente):
    activos = [nombre for nombre, on in gestor_eventos.estado().items() if on]
    if not activos: return
    etiquetas = {
        "hora_pico": ("HORA PICO", (245, 190,  50)),
        "lluvia":    ("LLUVIA",    (130, 180, 230)),
        "niebla":    ("NIEBLA",    (190, 200, 190)),
        "accidente": ("ACCIDENTE", (255,  80,  80)),
        "noche":     ("NOCHE",     ( 80, 100, 200)),
        "fiesta":    ("FIESTA",    (255,  80, 180)),
    }
    py = 10
    for nombre in activos:
        texto, color = etiquetas.get(nombre, (nombre.upper(), (200, 200, 200)))
        surf = fuente.render(texto, True, color)
        bg   = _pg.Surface((surf.get_width() + 10, surf.get_height() + 4), _pg.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        pantalla.blit(bg,   (8,  py - 2))
        pantalla.blit(surf, (13, py))
        py += surf.get_height() + 6
