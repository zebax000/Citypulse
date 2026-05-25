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


