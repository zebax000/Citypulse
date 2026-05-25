# main.py
import pygame
import sys
from core.simulacion import GestorSimulacion
from ui import renderer


class App:
    ANCHO_SIM   = 1280
    ALTO        = 720
    ANCHO_PANEL = 320

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("CityPulse – Simulador de Tráfico Urbano")
        self.ventana        = pygame.display.set_mode((self.ANCHO_SIM + self.ANCHO_PANEL, self.ALTO))
        self.superficie_sim = pygame.Surface((self.ANCHO_SIM, self.ALTO))
        self.reloj          = pygame.time.Clock()
        self.fuente_titulo  = pygame.font.SysFont("consolas", 22, bold=True)
        self.fuente_texto   = pygame.font.SysFont("consolas", 16)
        self.gestor         = GestorSimulacion()
        self.corriendo      = True
        self.debug          = False

    def _manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False

            if evento.type == pygame.KEYDOWN:
                g = self.gestor
                match evento.key:
                    case pygame.K_ESCAPE:
                        self.corriendo = False
                    case pygame.K_SPACE:
                        g.pausar_reanudar()
                    case pygame.K_1:
                        g.cambiar_escenario(0)
                    case pygame.K_2:
                        g.cambiar_escenario(1)
                    case pygame.K_3:
                        g.cambiar_escenario(2)
                    case pygame.K_4:
                        g.cambiar_escenario(3)
                    case pygame.K_PLUS | pygame.K_KP_PLUS | pygame.K_EQUALS:
                        g.ajustar_escala(g.escala_tiempo + 0.25)
                    case pygame.K_MINUS | pygame.K_KP_MINUS:
                        g.ajustar_escala(g.escala_tiempo - 0.25)
                    case pygame.K_r:
                        g.recargar_escenarios()
                    case pygame.K_t:
                        g.gestor_eventos.toggle("hora_pico", g)
                    case pygame.K_y:
                        g.gestor_eventos.toggle("lluvia", g)
                    case pygame.K_u:
                        g.gestor_eventos.toggle("accidente", g)
                    case pygame.K_i:
                        g.gestor_eventos.toggle("niebla", g)
                    case pygame.K_o:
                        g.gestor_eventos.toggle("noche", g)
                    case pygame.K_f:
                        g.gestor_eventos.toggle("fiesta", g)
                    case pygame.K_F1:
                        self.debug = not self.debug
                        print(f"[DEBUG] {'ON' if self.debug else 'OFF'}")

            elif evento.type == pygame.MOUSEWHEEL:
                if pygame.mouse.get_pos()[0] >= self.ANCHO_SIM:
                    from ui.renderer import panel_scroll
                    panel_scroll(evento.y)

    def ejecutar(self):
        while self.corriendo:
            dt_real = self.reloj.tick(60) / 1000.0

            self._manejar_eventos()
            self.gestor.actualizar(dt_real)

            renderer.dibujar_escenario(self.superficie_sim, self.gestor.escenario)
            renderer.dibujar_vehiculos(self.superficie_sim, self.gestor.escenario)
            renderer.dibujar_eventos(
                self.superficie_sim,
                self.gestor.gestor_eventos,
                self.ANCHO_SIM,
                self.ALTO,
                self.gestor.escenario,
            )
            renderer.dibujar_nombre_eventos(
                self.superficie_sim,
                self.gestor.gestor_eventos,
                self.fuente_texto,
            )
            if self.debug:
                from ui import debug
                debug.dibujar_debug(self.superficie_sim, self.gestor.escenario)

            self.ventana.blit(self.superficie_sim, (0, 0))
            renderer.dibujar_panel(
                self.ventana, self.gestor,
                x=self.ANCHO_SIM, ancho=self.ANCHO_PANEL, alto=self.ALTO,
                fuente_titulo=self.fuente_titulo, fuente_texto=self.fuente_texto,
                debug_activo=self.debug,
            )

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App().ejecutar()
