import pygame
import sys

from core.logica import GestorSimulacion


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("CityPulse - Simulador de Movilidad Urbana")

        self.ancho_simulacion = 1280
        self.alto = 720
        self.ancho_panel = 320

        self.ventana = pygame.display.set_mode((self.ancho_simulacion + self.ancho_panel, self.alto))
        self.superficie_simulacion = pygame.Surface((self.ancho_simulacion, self.alto))
        self.reloj = pygame.time.Clock()

        self.fuente_titulo = pygame.font.SysFont("consolas", 22, bold=True)
        self.fuente_texto = pygame.font.SysFont("consolas", 16)

        self.gestor = GestorSimulacion()
        self.ejecutando = True

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.ejecutando = False

                elif evento.key == pygame.K_SPACE:
                    self.gestor.pausar_reanudar()

                elif evento.key == pygame.K_1:
                    self.gestor.cambiar_escenario(0)

                elif evento.key == pygame.K_2:
                    self.gestor.cambiar_escenario(1)

                elif evento.key == pygame.K_3:
                    self.gestor.cambiar_escenario(2)

                elif evento.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                    self.gestor.ajustar_escala(self.gestor.escala_tiempo + 0.25)

                elif evento.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.gestor.ajustar_escala(self.gestor.escala_tiempo - 0.25)

                elif evento.key == pygame.K_r:
                    self.gestor.recargar_escenarios()

    def ejecutar(self):
        while self.ejecutando:
            dt_real = self.reloj.tick(60) / 1000.0

            self.manejar_eventos()
            self.gestor.actualizar(dt_real)

            self.gestor.dibujar(self.superficie_simulacion)
            self.ventana.blit(self.superficie_simulacion, (0, 0))

            self.gestor.dibujar_panel(
                pantalla=self.ventana,
                x_inicio=self.ancho_simulacion,
                ancho_panel=self.ancho_panel,
                alto_total=self.alto,
                fuente_titulo=self.fuente_titulo,
                fuente_texto=self.fuente_texto
            )

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App().ejecutar()