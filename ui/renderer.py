# core/renderer.py
import math
import pygame

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


def _dibujar_via(pantalla, via):
    rect = pygame.Rect(via.x, via.y, via.ancho, via.alto)
    pygame.draw.rect(pantalla, COLOR_VIA,   rect)
    pygame.draw.rect(pantalla, COLOR_BORDE, rect, 2)
    if via.linea_central:
        if via.orientacion == "horizontal":
            cy = via.y + via.alto // 2
            pygame.draw.line(pantalla, COLOR_LINEA_AMARILLA,
                             (via.x, cy), (via.x + via.ancho, cy), 3)
        else:
            cx = via.x + via.ancho // 2
            pygame.draw.line(pantalla, COLOR_LINEA_AMARILLA,
                             (cx, via.y), (cx, via.y + via.alto), 3)
    for linea in via.lineas_separacion:
        if linea["orientacion"] == "horizontal":
            y = linea["pos"]
            x = via.x + 10
            while x < via.x + via.ancho - 10:
                pygame.draw.line(pantalla, COLOR_LINEA_BLANCA, (x, y), (x + 24, y), 2)
                x += 40
        else:
            x = linea["pos"]
            y = via.y + 10
            while y < via.y + via.alto - 10:
                pygame.draw.line(pantalla, COLOR_LINEA_BLANCA, (x, y), (x, y + 24), 2)
                y += 40


def _dibujar_cebra(pantalla: pygame.Surface, cebra) -> None:
    #acá la base = tamaño de la cebra (ancho o alto) y la franja = proporcional (8% del tamaño)
    # el espacio = proporcional (6%) Y con max(4, ...) evitamos que quede demasiado delgado.
    base = min(cebra.ancho, cebra.alto)

    franja = max(4, int(base * 0.08))
    espacio = max(4, int(base * 0.06))

    if cebra.ancho >= cebra.alto:
        xx = cebra.x
        while xx < cebra.x + cebra.ancho:
            pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA,
                             (xx, cebra.y, franja, cebra.alto))
            xx += franja + espacio
    else:
        yy = cebra.y
        while yy < cebra.y + cebra.alto:
            pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA,
                             (cebra.x, yy, cebra.ancho, franja))
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

    for nombre, lx, ly in luces:
        color = _COLORES_SEMAFORO[nombre] if nombre == estado else _APAGADO
        pygame.draw.circle(pantalla, color, (lx, ly), 8)

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


def dibujar_escenario(pantalla, escenario):
    pantalla.fill(COLOR_FONDO)
    for via in escenario.vias:
        _dibujar_via(pantalla, via)
    for cebra in escenario.cebras:
        _dibujar_cebra(pantalla, cebra)
    for lp in escenario.lineas_pare:
        _dibujar_linea_pare(pantalla, lp)
    for semaforo in escenario.semaforos:
        estado   = escenario.controlador.estado_grupo(semaforo.grupo)
        restante = escenario.controlador.tiempo_restante_grupo(semaforo.grupo)
        _dibujar_semaforo(pantalla, semaforo, estado, restante)


def dibujar_vehiculos(pantalla, escenario):
    for carril in escenario.carriles:
        for v in carril.vehiculos:
            # Posición lógica base
            x, y = v.posicion_px()

            # Offset de lane change (converge a 0)
            offset_cambio   = int(getattr(v, "offset_lateral",  0.0))
            # Offset Fase E (posicion_lateral — inactivo hasta Fase E)
            ancho_px_carril = getattr(carril, "ancho_carril_px", 0)
            pos_lat         = getattr(v, "posicion_lateral",    0.0)
            offset_posicion = int(pos_lat * ancho_px_carril / 2)
            offset_total    = offset_cambio + offset_posicion

            if carril.eje == "x":
                y += offset_total
            else:
                x += offset_total

            # Surface con rotación visual aplicada
            surf = _render_vehiculo_surface(v, carril)

            # Centrar el bounding box rotado sobre (x, y)
            rect = surf.get_rect(center=(x, y))

            pantalla.blit(surf, rect)


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
                color_borde = (255, 30, 30)
            else:
                color_borde = {
                    "LIBRE":      (80,  80,  80),
                    "PREPARANDO": (255, 200,   0),
                    "CAMBIANDO":  (  0, 200, 255),
                }.get(estado, (255, 0, 0))

            # Hitbox lógico — NO rotado, siempre estable para debug
            ancho_px = v.ancho if carril.eje == "x" else v.alto
            alto_px  = v.alto  if carril.eje == "x" else v.ancho
            rect_logico = pygame.Rect(0, 0, ancho_px, alto_px)
            rect_logico.center = (x, y)
            pygame.draw.rect(pantalla, color_borde, rect_logico, 2)

            # Línea visual→lógico si hay offset
            bx, by = v.posicion_px()
            if abs(bx - x) > 2 or abs(by - y) > 2:
                pygame.draw.line(pantalla, (255, 60, 60), (x, y), (bx, by), 1)

            # Etiqueta con ángulo visual para debug
            vid      = id(v)
            t_prep   = _d_tiempos_estado.get(vid, (None, 0.0))[1]
            intentos = sum(getattr(v, "_intentos_fallidos", {}).values())
            off_val  = getattr(v, "offset_lateral", 0.0)
            ang_val  = getattr(v, "angulo_visual",  0.0)

            label = f"{v.id[-3:]} {estado[0]}"
            if abs(off_val) > 0.5:
                label += f" {off_val:+.0f}"
            if abs(ang_val) > 0.3:
                label += f" {ang_val:+.1f}°"
            if intentos > 0:
                label += f" !{intentos}"
            if estado == "PREPARANDO" and t_prep > 1.0:
                label += f" {t_prep:.1f}s"

            surf = fuente.render(label, True, color_borde)
            pantalla.blit(surf, (rect_logico.left, rect_logico.top - 12))

    errores = debug_historial(8)
    if errores:
        py = pantalla.get_height() - 14 * len(errores) - 8
        for err in errores:
            color = (255, 80, 80) if any(
                tag in err for tag in
                ("DOBLE", "OVERLAP", "NAN", "INV", "OWNERSHIP", "ZOMBIE")
            ) else (255, 200, 0)
            surf = fuente.render(err[:72], True, color)
            pantalla.blit(surf, (8, py))
            py += 14

    perf  = debug_perf()
    cont  = debug_contadores()
    frame = getattr(gestor, "_frame_n", 0)

    lineas_perf = [
        f"frame #{frame}",
        f"semaforos  {perf.get('semaforos', 0):.2f}ms",
        f"spawn      {perf.get('spawn', 0):.2f}ms",
        f"lc_intent  {perf.get('lane_change_intent', 0):.2f}ms",
        f"fisica     {perf.get('fisica', 0):.2f}ms",
        f"metricas   {perf.get('metricas', 0):.2f}ms",
        f"activos    {cont.get('vehiculos_en_listas', 0)}",
        f"err frames {cont.get('frames_con_error', 0)}",
    ]

    px_r = pantalla.get_width() - 162
    py_r = 8
    bg   = pygame.Surface((158, len(lineas_perf) * 14 + 8), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 140))
    pantalla.blit(bg, (px_r - 4, py_r - 4))
    for linea in lineas_perf:
        surf = fuente.render(linea, True, (180, 255, 180))
        pantalla.blit(surf, (px_r, py_r))
        py_r += 14


def dibujar_panel(pantalla, gestor, x, ancho, alto, fuente_titulo, fuente_texto):
    pygame.draw.rect(pantalla, COLOR_PANEL, pygame.Rect(x, 0, ancho, alto))

    m    = gestor.metricas
    esc  = gestor.escenario
    ctrl = esc.controlador

    try:
        from core.simulacion import DEBUG_ACTIVO, DEBUG_OVERLAY, debug_contadores
        dbg_on    = DEBUG_ACTIVO
        ovl_on    = DEBUG_OVERLAY
        err_total = debug_contadores().get("frames_con_error", 0)
    except ImportError:
        dbg_on, ovl_on, err_total = False, False, 0

    lineas = [
        ("CityPulse",                                        fuente_titulo),
        ("",                                                 None),
        (f"Escenario: {esc.nombre[:22]}",                    fuente_texto),
        (f"Pausado: {'Si' if gestor.pausado else 'No'}",      fuente_texto),
        (f"Velocidad: {gestor.escala_tiempo:.2f}x",          fuente_texto),
        ("",                                                 None),
        (f"Activos: {m['activos']}",                         fuente_texto),
        (f"Generados: {m['generados']}",                     fuente_texto),
        (f"Salidos: {m['salidos']}",                         fuente_texto),
        (f"Vel. prom: {m['velocidad_promedio']:.1f}",        fuente_texto),
        (f"Cola: {m['cola_total']}",                         fuente_texto),
        ("",                                                 None),
        (f"Congestion: {m['carriles_congestionados']} carr.", fuente_texto),
        (f"Espera prom: {m['tiempo_espera_promedio']:.1f}s",  fuente_texto),
        (f"Prioritarios: {m['prioritarios_activos']}",        fuente_texto),
        ("",                                                 None),
        (f"H: {ctrl.estado_grupo('H')} "
         f"({ctrl.tiempo_restante_grupo('H'):.1f}s)",        fuente_texto),
        (f"V: {ctrl.estado_grupo('V')} "
         f"({ctrl.tiempo_restante_grupo('V'):.1f}s)",        fuente_texto),
        ("",                                                 None),
        (f"Debug: {'ON' if dbg_on else 'OFF'}  "
         f"Overlay: {'ON' if ovl_on else 'OFF'}",            fuente_texto),
        (f"Err frames: {err_total}",                         fuente_texto),
        ("",                                                 None),
        ("Controles:",                                       fuente_texto),
        ("1/2/3  escenario",                                 fuente_texto),
        ("SPACE  pausar",                                    fuente_texto),
        ("+/-    velocidad",                                 fuente_texto),
        ("R      recargar",                                  fuente_texto),
        ("D      overlay debug",                             fuente_texto),
        ("F1     dump errores",                              fuente_texto),
        ("ESC    salir",                                     fuente_texto),
    ]

    px, py = x + 16, 16
    for texto, fuente in lineas:
        if fuente is None:
            py += 10
            continue
        surf = fuente.render(texto, True, COLOR_TEXTO)
        pantalla.blit(surf, (px, py))
        py += surf.get_height() + 6
