import os
import json
import pygame


COLOR_FONDO = (62, 135, 76)
COLOR_VIA = (45, 45, 45)
COLOR_BORDE = (92, 92, 92)
COLOR_LINEA_AMARILLA = (255, 204, 0)
COLOR_LINEA_BLANCA = (245, 245, 245)


class Cebra:
    def __init__(self, x, y, ancho, alto):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto

    def dibujar(self, pantalla):
        franja = 8
        espacio = 6

        if self.ancho >= self.alto:
            xx = self.x
            while xx < self.x + self.ancho:
                pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA, (xx, self.y, franja, self.alto))
                xx += franja + espacio
        else:
            yy = self.y
            while yy < self.y + self.alto:
                pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA, (self.x, yy, self.ancho, franja))
                yy += franja + espacio


class LineaPare:
    def __init__(self, x, y, ancho, alto):
        self.rect = pygame.Rect(x, y, ancho, alto)

    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, COLOR_LINEA_BLANCA, self.rect)


class Via:
    def __init__(self, x, y, ancho, alto, orientacion, lineas_separacion=None, linea_central=True):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.orientacion = orientacion
        self.lineas_separacion = lineas_separacion or []
        self.linea_central = linea_central

    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, COLOR_VIA, self.rect)
        pygame.draw.rect(pantalla, COLOR_BORDE, self.rect, 2)

        if self.linea_central:
            if self.orientacion == "horizontal":
                cy = self.rect.y + self.rect.h // 2
                pygame.draw.line(
                    pantalla,
                    COLOR_LINEA_AMARILLA,
                    (self.rect.x, cy),
                    (self.rect.x + self.rect.w, cy),
                    3
                )
            else:
                cx = self.rect.x + self.rect.w // 2
                pygame.draw.line(
                    pantalla,
                    COLOR_LINEA_AMARILLA,
                    (cx, self.rect.y),
                    (cx, self.rect.y + self.rect.h),
                    3
                )

        for linea in self.lineas_separacion:
            if linea["orientacion"] == "horizontal":
                y = linea["pos"]
                x = self.rect.x + 10
                while x < self.rect.x + self.rect.w - 10:
                    pygame.draw.line(pantalla, COLOR_LINEA_BLANCA, (x, y), (x + 24, y), 2)
                    x += 40
            else:
                x = linea["pos"]
                y = self.rect.y + 10
                while y < self.rect.y + self.rect.h - 10:
                    pygame.draw.line(pantalla, COLOR_LINEA_BLANCA, (x, y), (x, y + 24), 2)
                    y += 40


class Carril:
    def __init__(
        self,
        id_carril,
        eje,
        coordenada_fija,
        direccion,
        inicio,
        fin,
        coord_pare,
        grupo_semaforo,
        spawn_intervalo=1.5,
        mezcla_vehiculos=None
    ):
        self.id_carril = id_carril
        self.eje = eje
        self.coordenada_fija = coordenada_fija
        self.direccion = direccion
        self.inicio = inicio
        self.fin = fin
        self.coord_pare = coord_pare
        self.grupo_semaforo = grupo_semaforo
        self.spawn_intervalo = spawn_intervalo
        self.mezcla_vehiculos = mezcla_vehiculos or {
            "automovil": 0.40,
            "moto": 0.28,
            "bus": 0.15,
            "camion": 0.17
        }

        self.vehiculos = []
        self.temporizador_spawn = 0.0

        self.longitud_total = abs(self.fin - self.inicio)
        self.progreso_pare = abs(self.coord_pare - self.inicio)

        # El frente del vehículo debe detenerse ANTES de esta línea
        self.margen_detencion = 14

    def posicion_mundo(self, progreso):
        if self.direccion > 0:
            coord = self.inicio + progreso
        else:
            coord = self.inicio - progreso

        if self.eje == "x":
            return int(coord), int(self.coordenada_fija)
        return int(self.coordenada_fija), int(coord)


class Semaforo:
    def __init__(self, id_s, x, y, grupo, lado="centro"):
        self.id_s = id_s
        self.x = x
        self.y = y
        self.grupo = grupo
        self.lado = lado
        self._fuente = None

    def dibujar(self, pantalla, estado_actual, restante):
        if self._fuente is None:
            self._fuente = pygame.font.SysFont("consolas", 16, bold=True)

        # cuerpo del semáforo fuera de la vía según "lado"
        ancho_caja = 24
        alto_caja = 64

        if self.lado == "izquierda":
            cuerpo = pygame.Rect(self.x - ancho_caja - 6, self.y - alto_caja // 2, ancho_caja, alto_caja)
            pygame.draw.line(pantalla, (80, 80, 80), (self.x, self.y), (self.x - 6, self.y), 3)
        elif self.lado == "derecha":
            cuerpo = pygame.Rect(self.x + 6, self.y - alto_caja // 2, ancho_caja, alto_caja)
            pygame.draw.line(pantalla, (80, 80, 80), (self.x, self.y), (self.x + 6, self.y), 3)
        elif self.lado == "arriba":
            cuerpo = pygame.Rect(self.x - ancho_caja // 2, self.y - alto_caja - 6, ancho_caja, alto_caja)
            pygame.draw.line(pantalla, (80, 80, 80), (self.x, self.y), (self.x, self.y - 6), 3)
        elif self.lado == "abajo":
            cuerpo = pygame.Rect(self.x - ancho_caja // 2, self.y + 6, ancho_caja, alto_caja)
            pygame.draw.line(pantalla, (80, 80, 80), (self.x, self.y), (self.x, self.y + 6), 3)
        else:
            cuerpo = pygame.Rect(self.x - 12, self.y - 32, ancho_caja, alto_caja)

        pygame.draw.rect(pantalla, (30, 30, 30), cuerpo, border_radius=5)
        pygame.draw.rect(pantalla, (10, 10, 10), cuerpo, 2, border_radius=5)

        colores = {
            "ROJO": (220, 40, 40),
            "AMARILLO": (255, 185, 0),
            "VERDE": (40, 200, 80)
        }

        cx = cuerpo.centerx
        focos = [
            ("ROJO", cuerpo.y + 15),
            ("AMARILLO", cuerpo.y + 32),
            ("VERDE", cuerpo.y + 49)
        ]
        for nombre, fy in focos:
            color = colores[nombre] if nombre == estado_actual else (70, 70, 70)
            pygame.draw.circle(pantalla, color, (cx, fy), 8)

        txt = self._fuente.render(str(max(0, int(restante + 0.999))), True, (255, 255, 255))
        rect_txt = txt.get_rect(center=(cuerpo.centerx, cuerpo.bottom + 14))
        pantalla.blit(txt, rect_txt)


class ControladorCruce:
    """
    Fases estrictas:
      1. HORIZONTAL_VERDE
      2. HORIZONTAL_AMARILLO
      3. VERTICAL_VERDE
      4. VERTICAL_AMARILLO

    Nunca hay verde simultáneo para H y V.
    """
    def __init__(self, verde_h, amarillo_h, verde_v, amarillo_v):
        self.verde_h = float(verde_h)
        self.amarillo_h = float(amarillo_h)
        self.verde_v = float(verde_v)
        self.amarillo_v = float(amarillo_v)

        self.fase = "HORIZONTAL_VERDE"
        self.timer = 0.0

    def actualizar(self, dt):
        self.timer += dt
        duracion = self._duracion_actual()

        while self.timer >= duracion:
            self.timer -= duracion
            if self.fase == "HORIZONTAL_VERDE":
                self.fase = "HORIZONTAL_AMARILLO"
            elif self.fase == "HORIZONTAL_AMARILLO":
                self.fase = "VERTICAL_VERDE"
            elif self.fase == "VERTICAL_VERDE":
                self.fase = "VERTICAL_AMARILLO"
            else:
                self.fase = "HORIZONTAL_VERDE"
            duracion = self._duracion_actual()

    def _duracion_actual(self):
        if self.fase == "HORIZONTAL_VERDE":
            return self.verde_h
        if self.fase == "HORIZONTAL_AMARILLO":
            return self.amarillo_h
        if self.fase == "VERTICAL_VERDE":
            return self.verde_v
        return self.amarillo_v

    def estado_grupo(self, grupo):
        if grupo == "H":
            if self.fase == "HORIZONTAL_VERDE":
                return "VERDE"
            if self.fase == "HORIZONTAL_AMARILLO":
                return "AMARILLO"
            return "ROJO"

        if self.fase == "VERTICAL_VERDE":
            return "VERDE"
        if self.fase == "VERTICAL_AMARILLO":
            return "AMARILLO"
        return "ROJO"

    def tiempo_restante_grupo(self, grupo):
        """
        Tiempo restante DEL ESTADO ACTUAL de ese grupo.
        """
        if grupo == "H":
            if self.fase == "HORIZONTAL_VERDE":
                return self.verde_h - self.timer
            if self.fase == "HORIZONTAL_AMARILLO":
                return self.amarillo_h - self.timer
            if self.fase == "VERTICAL_VERDE":
                return (self.verde_v - self.timer) + self.amarillo_v
            return self.amarillo_v - self.timer

        if self.fase == "VERTICAL_VERDE":
            return self.verde_v - self.timer
        if self.fase == "VERTICAL_AMARILLO":
            return self.amarillo_v - self.timer
        if self.fase == "HORIZONTAL_VERDE":
            return (self.verde_h - self.timer) + self.amarillo_h
        return self.amarillo_h - self.timer


class Escenario:
    def __init__(self, data):
        self.nombre = data["nombre"]
        self.ancho = data.get("ancho", 1280)
        self.alto = data.get("alto", 720)

        control = data["controlador"]
        self.controlador = ControladorCruce(
            verde_h=control["verde_h"],
            amarillo_h=control["amarillo_h"],
            verde_v=control["verde_v"],
            amarillo_v=control["amarillo_v"]
        )

        self.vias = [
            Via(
                x=v["x"],
                y=v["y"],
                ancho=v["ancho"],
                alto=v["alto"],
                orientacion=v["orientacion"],
                lineas_separacion=v.get("lineas_separacion", []),
                linea_central=v.get("linea_central", True)
            )
            for v in data.get("vias", [])
        ]

        self.cebras = [
            Cebra(z["x"], z["y"], z["ancho"], z["alto"])
            for z in data.get("cebras", [])
        ]

        self.lineas_pare = [
            LineaPare(lp["x"], lp["y"], lp["ancho"], lp["alto"])
            for lp in data.get("lineas_pare", [])
        ]

        self.semaforos = [
            Semaforo(
                id_s=s["id"],
                x=s["x"],
                y=s["y"],
                grupo=s["grupo"],
                lado=s.get("lado", "centro")
            )
            for s in data.get("semaforos", [])
        ]

        self.carriles = [
            Carril(
                id_carril=c["id_carril"],
                eje=c["eje"],
                coordenada_fija=c["coordenada_fija"],
                direccion=c["direccion"],
                inicio=c["inicio"],
                fin=c["fin"],
                coord_pare=c["coord_pare"],
                grupo_semaforo=c["grupo_semaforo"],
                spawn_intervalo=c.get("spawn_intervalo", 1.5),
                mezcla_vehiculos=c.get("mezcla_vehiculos")
            )
            for c in data.get("carriles", [])
        ]

    def actualizar(self, dt):
        self.controlador.actualizar(dt)

    def estado_semaforo_para_carril(self, carril):
        return self.controlador.estado_grupo(carril.grupo_semaforo)

    def dibujar(self, pantalla):
        pantalla.fill(COLOR_FONDO)

        for via in self.vias:
            via.dibujar(pantalla)

        for cebra in self.cebras:
            cebra.dibujar(pantalla)

        for linea in self.lineas_pare:
            linea.dibujar(pantalla)

        for semaforo in self.semaforos:
            estado = self.controlador.estado_grupo(semaforo.grupo)
            restante = self.controlador.tiempo_restante_grupo(semaforo.grupo)
            semaforo.dibujar(pantalla, estado, restante)


def cargar_escenarios(carpeta_escenarios):
    escenarios = []

    if not os.path.exists(carpeta_escenarios):
        raise FileNotFoundError(f"No existe la carpeta de escenarios: {carpeta_escenarios}")

    archivos = sorted([a for a in os.listdir(carpeta_escenarios) if a.endswith(".json")])

    for archivo in archivos:
        ruta = os.path.join(carpeta_escenarios, archivo)
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
            escenarios.append(Escenario(data))

    if not escenarios:
        raise RuntimeError("No se encontraron escenarios .json en data/escenarios/")

    return escenarios
