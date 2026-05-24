#Main para el correcto funcionamiento: 
import pygame
import sys
from core.simulacion import GestorSimulacion
from ui import renderer

DEBUG = False
class App:
    ANCHO_SIM   = 1280
    ALTO        = 720
    ANCHO_PANEL = 320

    def __init__(self):

        pygame.init()
        #logo favicon
        icono = pygame.image.load("assets/ui/citypulse_logo.png")
        pygame.display.set_icon(icono)

        pygame.display.set_caption("CityPulse – Simulador de Tráfico Urbano")
        self.ventana = pygame.display.set_mode((self.ANCHO_SIM + self.ANCHO_PANEL, self.ALTO))
        self.superficie_sim = pygame.Surface((self.ANCHO_SIM, self.ALTO))
        self.reloj = pygame.time.Clock()

        #carga de ssonido
        pygame.mixer.init()
        pygame.mixer.music.load("assets/audio/trafico.ogg")
        pygame.mixer.music.set_volume(0.20)  # 20%, para que sea sutil
        pygame.mixer.music.play(-1)  # bucle infinito

        pygame.display.set_caption("CityPulse – Simulador de Tráfico Vehicular Urbano")
        self.ventana = pygame.display.set_mode((self.ANCHO_SIM + self.ANCHO_PANEL, self.ALTO))
        self.superficie_sim = pygame.Surface((self.ANCHO_SIM, self.ALTO))
        self.reloj = pygame.time.Clock()

        self.fuente_titulo = pygame.font.SysFont("consolas", 22, bold=True)
        self.fuente_texto  = pygame.font.SysFont("consolas", 16)

        self.gestor = GestorSimulacion()
        self.corriendo = True

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
                    case pygame.K_PLUS | pygame.K_KP_PLUS | pygame.K_EQUALS:
                        g.ajustar_escala(g.escala_tiempo + 0.25)
                    case pygame.K_MINUS | pygame.K_KP_MINUS:
                        g.ajustar_escala(g.escala_tiempo - 0.25)
                    case pygame.K_r:
                        g.recargar_escenarios()

    def ejecutar(self):
        while self.corriendo:
            dt_real = self.reloj.tick(60) / 1000.0

            self._manejar_eventos()
            self.gestor.actualizar(dt_real)

            renderer.dibujar_escenario(self.superficie_sim, self.gestor.escenario)
            renderer.dibujar_vehiculos(self.superficie_sim, self.gestor.escenario)

            # ── BLOQUE NUEVO ─────────────────────────────────────────────
            if DEBUG:
                from ui import debug
                debug.dibujar_debug(self.superficie_sim, self.gestor.escenario)
            # ─────────────────────────────────────────────────────────────

            self.ventana.blit(self.superficie_sim, (0, 0))
            renderer.dibujar_panel(
                self.ventana, self.gestor,
                x=self.ANCHO_SIM, ancho=self.ANCHO_PANEL, alto=self.ALTO,
                fuente_titulo=self.fuente_titulo, fuente_texto=self.fuente_texto
            )
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App().ejecutar()
