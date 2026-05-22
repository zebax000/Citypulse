# ui/debug.py
# Renderizado de debug. Solo se usa con DEBUG=True en main.py.
# No modifica renderer.py ni core/.
import pygame

COLOR_FRENTE   = (255, 80,  80,  160)
COLOR_COLA     = (80,  80,  255, 160)
COLOR_PARE     = (255, 255, 0,   200)
COLOR_CAJA     = (255, 255, 255, 60)


def dibujar_debug(pantalla: pygame.Surface, escenario) -> None:
    for carril in escenario.carriles:
        # Línea de pare
        px, py = carril.posicion_mundo(carril.progreso_pare)
        if carril.eje == "x":
            pygame.draw.line(pantalla, COLOR_PARE, (px, py - 20), (px, py + 20), 2)
        else:
            pygame.draw.line(pantalla, COLOR_PARE, (px - 20, py), (px + 20, py), 2)

        for v in carril.vehiculos:
            x, y = v.posicion_px()
            w = v.ancho if carril.eje == "x" else v.alto
            h = v.alto  if carril.eje == "x" else v.ancho
            # Caja del vehículo
            rect = pygame.Rect(0, 0, w, h)
            rect.center = (x, y)
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill(COLOR_CAJA)
            pantalla.blit(s, rect)
            pygame.draw.rect(pantalla, (255, 255, 255), rect, 1)
            # Punto de frente y cola
            fx, fy = carril.posicion_mundo(v.frente_progreso())
            cx2, cy2 = carril.posicion_mundo(v.cola_progreso())
            pygame.draw.circle(pantalla, COLOR_FRENTE[:3], (fx, fy), 3)
            pygame.draw.circle(pantalla, COLOR_COLA[:3],   (cx2, cy2), 3)
