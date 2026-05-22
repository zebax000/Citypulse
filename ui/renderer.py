#Dibuja todo en pygame: vías, cebras, líneas de pare, semáforos con rotación por eje, vehículos con sprites, contadores de tiempo
import pygame

# ── paleta ────────────────────────────────────────────────────────────────
COLOR_FONDO          = (62, 135, 76)
COLOR_VIA            = (45, 45, 45)
COLOR_BORDE          = (92, 92, 92)
COLOR_LINEA_AMARILLA = (255, 204, 0)
COLOR_LINEA_BLANCA   = (245, 245, 245)
COLOR_PANEL          = (25, 25, 30)
COLOR_TEXTO          = (235, 235, 235)

_COLORES_SEMAFORO = {"ROJO": (220, 40, 40), "AMARILLO": (255, 185, 0), "VERDE": (40, 200, 80)}
_APAGADO = (70, 70, 70)
_SEM_GAP        = 8    # distancia entre borde de vía y caja del semáforo
_SEM_TEXTO_GAP  = 7   # distancia entre caja del semáforo y su número

_fuente_semaforo: pygame.font.Font | None = None


def _get_fuente_semaforo():
    global _fuente_semaforo
    if _fuente_semaforo is None:
        _fuente_semaforo = pygame.font.SysFont("consolas", 16, bold=True)
    return _fuente_semaforo


# ── infraestructura ────────────────────────────────────────────────────────

def _dibujar_via(pantalla: pygame.Surface, via) -> None:
    rect = pygame.Rect(via.x, via.y, via.ancho, via.alto)
    pygame.draw.rect(pantalla, COLOR_VIA, rect)
    pygame.draw.rect(pantalla, COLOR_BORDE, rect, 2)

    if via.linea_central:
        if via.orientacion == "horizontal":
            cy = via.y + via.alto // 2
            pygame.draw.line(pantalla, COLOR_LINEA_AMARILLA, (via.x, cy), (via.x + via.ancho, cy), 3)
        else:
            cx = via.x + via.ancho // 2
            pygame.draw.line(pantalla, COLOR_LINEA_AMARILLA, (cx, via.y), (cx, via.y + via.alto), 3)

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
    franja, espacio = 8, 6
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


def _dibujar_linea_pare(pantalla: pygame.Surface, lp) -> None:
    pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA, pygame.Rect(lp.x, lp.y, lp.ancho, lp.alto))


def _dibujar_semaforo(pantalla: pygame.Surface, semaforo, estado: str, restante: float) -> None:
    fuente = _get_fuente_semaforo()

    # Dimensiones según orientación del grupo
    # H → semáforo "tumbado" (ancho > alto)
    # V → semáforo vertical (alto > ancho)
    es_horizontal = semaforo.grupo.startswith("H")
    if es_horizontal:
        ancho_caja, alto_caja = 64, 24   # tumbado
    else:
        ancho_caja, alto_caja = 24, 64   # vertical

    # Posición de la caja según lado
    lados = {
        "izquierda": pygame.Rect(semaforo.x - ancho_caja - _SEM_GAP,
                                  semaforo.y - alto_caja // 2, ancho_caja, alto_caja),
        "derecha":   pygame.Rect(semaforo.x + _SEM_GAP,
                                  semaforo.y - alto_caja // 2, ancho_caja, alto_caja),
        "arriba":    pygame.Rect(semaforo.x - ancho_caja // 2,
                                  semaforo.y - alto_caja - _SEM_GAP, ancho_caja, alto_caja),
        "abajo":     pygame.Rect(semaforo.x - ancho_caja // 2,
                                  semaforo.y + _SEM_GAP, ancho_caja, alto_caja),
    }
    cuerpo = lados.get(semaforo.lado,
                       pygame.Rect(semaforo.x - ancho_caja // 2,
                                   semaforo.y - alto_caja // 2, ancho_caja, alto_caja))

    # Caja
    pygame.draw.rect(pantalla, (30, 30, 30), cuerpo, border_radius=5)
    pygame.draw.rect(pantalla, (10, 10, 10), cuerpo, 2, border_radius=5)

    # Luces: posición según orientación
    # Horizontal → luces de izquierda a derecha (ROJO izq, AMARILLO centro, VERDE der)
    # Vertical   → luces de arriba a abajo     (ROJO arr, AMARILLO centro, VERDE abj)
    if es_horizontal:
        posiciones_luces = [
            ("ROJO",     cuerpo.x + 12,              cuerpo.centery),
            ("AMARILLO", cuerpo.x + ancho_caja // 2, cuerpo.centery),
            ("VERDE",    cuerpo.x + ancho_caja - 12, cuerpo.centery),
        ]
    else:
        posiciones_luces = [
            ("ROJO",     cuerpo.centerx, cuerpo.y + 12),
            ("AMARILLO", cuerpo.centerx, cuerpo.y + alto_caja // 2),
            ("VERDE",    cuerpo.centerx, cuerpo.y + alto_caja - 12),
        ]

    for nombre, lx, ly in posiciones_luces:
        color = _COLORES_SEMAFORO[nombre] if nombre == estado else _APAGADO
        pygame.draw.circle(pantalla, color, (lx, ly), 8)

    # Texto: hacia el exterior absoluto según orientación del grupo
    # Semáforos H (tumbados): texto siempre en el eje Y (arriba/abajo)
    # Semáforos V (verticales): texto siempre en el eje X (izquierda/derecha)
    txt = fuente.render(str(max(0, int(restante + 0.999))), True, COLOR_TEXTO)
    txt_rect = txt.get_rect()

    if es_horizontal:
        # H tumbado: texto va encima o debajo según lado, NUNCA al costado
        if semaforo.lado in ("arriba", "izquierda"):
            txt_rect.midbottom = (cuerpo.centerx, cuerpo.top - _SEM_TEXTO_GAP)
        else:
            txt_rect.midtop = (cuerpo.centerx, cuerpo.bottom + _SEM_TEXTO_GAP)
    else:
        # V vertical: texto va al costado según lado, NUNCA arriba/abajo
        if semaforo.lado in ("izquierda", "arriba"):
            txt_rect.midright = (cuerpo.left - _SEM_TEXTO_GAP, cuerpo.centery)
        else:
            txt_rect.midleft = (cuerpo.right + _SEM_TEXTO_GAP, cuerpo.centery)

    pantalla.blit(txt, txt_rect)

# ── funciones públicas ────────────────────────────────────────────────────

def dibujar_escenario(pantalla: pygame.Surface, escenario) -> None:
    """Dibuja toda la infraestructura del escenario activo."""
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


def dibujar_panel(pantalla: pygame.Surface, gestor, x: int, ancho: int, alto: int,
                  fuente_titulo: pygame.font.Font, fuente_texto: pygame.font.Font) -> None:
    """Dibuja el panel lateral con métricas y controles."""
    pygame.draw.rect(pantalla, COLOR_PANEL, pygame.Rect(x, 0, ancho, alto))

    m  = gestor.metricas
    esc = gestor.escenario
    ctrl = esc.controlador

    lineas = [
        ("CityPulse", fuente_titulo),
        ("", None),
        (f"Escenario: {esc.nombre[:22]}", fuente_texto),
        (f"Pausado:   {'Sí' if gestor.pausado else 'No'}", fuente_texto),
        (f"Velocidad: {gestor.escala_tiempo:.2f}x", fuente_texto),
        ("", None),
        (f"Activos:   {m['activos']}", fuente_texto),
        (f"Generados: {m['generados']}", fuente_texto),
        (f"Salidos:   {m['salidos']}", fuente_texto),
        (f"Vel. prom: {m['velocidad_promedio']:.1f}", fuente_texto),
        (f"Cola:      {m['cola_total']}", fuente_texto),
        ("", None),
        (f"H: {ctrl.estado_grupo('H')} ({ctrl.tiempo_restante_grupo('H'):.1f}s)", fuente_texto),
        (f"V: {ctrl.estado_grupo('V')} ({ctrl.tiempo_restante_grupo('V'):.1f}s)", fuente_texto),
        ("", None),
        ("Controles:", fuente_texto),
        ("1/2/3  escenario", fuente_texto),
        ("SPACE  pausar", fuente_texto),
        ("+/-    velocidad", fuente_texto),
        ("R      recargar", fuente_texto),
        ("ESC    salir", fuente_texto),
    ]

    px, py = x + 16, 16
    for texto, fuente in lineas:
        if fuente is None:
            py += 10
            continue
        surf = fuente.render(texto, True, COLOR_TEXTO)
        pantalla.blit(surf, (px, py))
        py += surf.get_height() + 6


# REEMPLAZA dibujar_vehiculos() completo

def dibujar_vehiculos(pantalla: pygame.Surface, escenario) -> None:
    for carril in escenario.carriles:
        for v in carril.vehiculos:
            x, y = v.posicion_px()
            ancho_px = v.ancho if carril.eje == "x" else v.alto
            alto_px  = v.alto  if carril.eje == "x" else v.ancho
            rect = pygame.Rect(0, 0, ancho_px, alto_px)
            rect.center = (x, y)

            # Intentar sprite; si no existe, usar rectángulo de color
            if hasattr(v, "image") and v.image is not None:
                pantalla.blit(v.image, rect)
            else:
                pygame.draw.rect(pantalla, v.color, rect, border_radius=4)
                pygame.draw.rect(pantalla, (20, 20, 20), rect, 1, border_radius=4)
