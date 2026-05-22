# core/vehiculos.py
import os
import math
import random

try:
    import pygame
    _PYGAME_DISPONIBLE = True
except ImportError:
    _PYGAME_DISPONIBLE = False

# ── constantes de física ───────────────────────────────────────────────────
DISTANCIA_SEGURIDAD = 22   # base fija — la dinámica parte de aquí
DISTANCIA_MINIMA    = 4    # clamp absoluto de emergencia, NUNCA se toca
ESPACIO_SPAWN       = 110

# ── ruta de sprites ────────────────────────────────────────────────────────
_RAIZ         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RUTA_SPRITES = os.path.join(_RAIZ, "assets", "sprites")

def _sprite_existe(nombre):
    return os.path.isfile(os.path.join(_RUTA_SPRITES, nombre))

def _elegir_sprite(candidatos):
    disponibles = [c for c in candidatos if _sprite_existe(c)]
    return random.choice(disponibles) if disponibles else None

def _cargar_imagen(nombre, ancho, alto, eje, direccion, color_respaldo):
    ruta = os.path.join(_RUTA_SPRITES, nombre) if nombre else None
    if ruta and os.path.isfile(ruta):
        try:
            img = pygame.image.load(ruta).convert_alpha()
            if eje == "x":
                img = pygame.transform.scale(img, (ancho, alto))
                if direccion < 0:
                    img = pygame.transform.flip(img, True, False)
            else:
                img = pygame.transform.scale(img, (ancho, alto))
                angulo = -90 if direccion > 0 else 90
                img = pygame.transform.rotate(img, angulo)
            return img
        except Exception:
            pass
    w = ancho if eje == "x" else alto
    h = alto  if eje == "x" else ancho
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill(color_respaldo)
    pygame.draw.rect(surf, (20, 20, 20), surf.get_rect(), 2, border_radius=4)
    return surf.convert_alpha()


# ── clase base ─────────────────────────────────────────────────────────────
class Vehiculo:
    VELOCIDAD_MAX   = 100.0
    ACELERACION     = 30.0
    FRENADO         = 100.0
    ANCHO           = 60
    ALTO            = 30
    COLOR_RESPALDO  = (200, 200, 200)
    SPRITES         = []

    def __init__(self, id_v, carril):
        self.id     = id_v
        self.carril = carril
        self.ancho  = self.ANCHO
        self.alto   = self.ALTO
        self.color  = self.COLOR_RESPALDO

        # ── personalidad individual ────────────────────────────────────────
        # Generada una sola vez al nacer. Todos los sistemas leen de aquí.
        # Rango moderado: evita extremos que producen comportamientos irreales.
        self.agresividad         = random.uniform(0.25, 0.90)
        self.tiempo_reaccion     = random.uniform(0.06, 0.20)   # segundos
        self.suavidad_frenado    = random.uniform(0.60, 1.00)   # 1.0 = muy suave
        self.tolerancia_amarillo = random.uniform(0.15, 0.65)   # 0=frena, 1=cruza

        # Acumulador interno del tiempo de reacción (no exponer al exterior)
        self._reaccion_acum      = 0.0
        self._vel_obj_retrasada  = 0.0   # "última percepción" del conductor

        # ── parámetros base ajustados por personalidad ─────────────────────
        # Agresividad sube velocidad y aceleración moderadamente.
        # suavidad_frenado reduce la capacidad de frenado (más humano).
        self.velocidad_max = (
            self.VELOCIDAD_MAX
            * random.uniform(0.88, 1.08)
            * (0.90 + self.agresividad * 0.15)
        )
        self.aceleracion = (
            self.ACELERACION
            * random.uniform(0.90, 1.10)
            * (0.85 + self.agresividad * 0.20)
        )
        # frenado NUNCA baja de FRENADO*0.75 para garantizar que puede frenar
        # antes de la línea de pare en cualquier escenario.
        self.frenado = self.FRENADO * max(0.75, 1.15 - self.suavidad_frenado * 0.40)

        self.velocidad_actual = random.uniform(
            self.velocidad_max * 0.40,
            self.velocidad_max * 0.65,
        )
        self._vel_obj_retrasada = self.velocidad_actual  # inicializar coherente

        self.progreso      = -self._largo()
        self.tiempo_espera = 0.0

        self.image = None
        if _PYGAME_DISPONIBLE:
            sprite = _elegir_sprite(self.SPRITES)
            self.image = _cargar_imagen(
                sprite, self.ancho, self.alto,
                carril.eje, carril.direccion, self.COLOR_RESPALDO,
            )

    # ── geometría ──────────────────────────────────────────────────────────
    def _largo(self):
        return self.ancho

    def frente_progreso(self):
        return self.progreso + self._largo() / 2

    def cola_progreso(self):
        return self.progreso - self._largo() / 2

    def _progreso_pare_activo(self):
        for pp in self.carril.progreso_pares:
            if self.frente_progreso() < pp:
                return pp
        return None

    def ya_cruzo_linea_de_pare(self):
        return self._progreso_pare_activo() is None

    def _limite_pare(self):
        pp = self._progreso_pare_activo()
        if pp is None:
            return float("inf")
        return pp - self.carril.margen_detencion

    def salio_del_mapa(self):
        return self.cola_progreso() > self.carril.longitud_total

    def posicion_px(self):
        return self.carril.posicion_mundo(self.progreso)

    # ── distancia de seguridad dinámica ────────────────────────────────────
    def _distancia_seguridad(self):
        """
        Distancia dinámica: crece con velocidad y baja con agresividad.
        - por_velocidad: 0.08 mantiene tráfico denso pero seguro.
        - clamp mínimo: DISTANCIA_SEGURIDAD * 0.5 — garantía física absoluta.
        Preparada para: congestión, cambio de carril (leer este valor externamente).
        """
        por_velocidad    = self.velocidad_actual * 0.08
        por_personalidad = (1.0 - self.agresividad) * 8.0
        return max(DISTANCIA_SEGURIDAD * 0.5, DISTANCIA_SEGURIDAD + por_velocidad + por_personalidad)

    # ── física ─────────────────────────────────────────────────────────────
    def _velocidad_objetivo(self, vehiculo_frente, estado_semaforo):
        """
        Calcula vel_obj real (sin retraso) — el retraso se aplica en actualizar().
        Retorna (vel_obj, limite_progreso | None).
        """
        objetivo = self.velocidad_max
        limite   = None

        # 1) Semáforo
        if estado_semaforo == "ROJO" and not self.ya_cruzo_linea_de_pare():
            limite = self._limite_pare()

        elif estado_semaforo == "AMARILLO" and not self.ya_cruzo_linea_de_pare():
            distancia_al_pare = self._limite_pare() - self.frente_progreso()
            # Decisión humana: frena si está lejos O si tiene baja tolerancia.
            # Cruza solo si está muy cerca Y tiene tolerancia alta.
            # Umbral 55px: distancia mínima realista para decidir cruzar.
            if distancia_al_pare > 55 or self.tolerancia_amarillo < 0.45:
                limite = self._limite_pare()
            # else: conductor tolerante y ya comprometido → cruza sin frenar

        # 2) Vehículo de adelante — distancia dinámica
        if vehiculo_frente is not None:
            limite_v = vehiculo_frente.cola_progreso() - self._distancia_seguridad()
            limite   = min(limite, limite_v) if limite is not None else limite_v

        # 3) Velocidad segura para frenar antes del límite
        if limite is not None:
            distancia = limite - self.frente_progreso()
            if distancia <= 0:
                return 0.0, limite
            velocidad_segura = math.sqrt(max(0.0, 2.0 * self.frenado * distancia))
            objetivo = min(objetivo, velocidad_segura)

        return objetivo, limite

    def actualizar(self, dt, vehiculo_frente, estado_semaforo):
        vel_obj, limite = self._velocidad_objetivo(vehiculo_frente, estado_semaforo)

        # ── tiempo de reacción ─────────────────────────────────────────────
        # Retrasa SOLO la percepción de la velocidad objetivo.
        # El conductor "no se entera" del cambio hasta que acumula tiempo_reaccion.
        # Nunca afecta clamps de emergencia (están abajo, fuera de este bloque).
        self._reaccion_acum += dt
        if self._reaccion_acum >= self.tiempo_reaccion:
            self._reaccion_acum      = 0.0
            self._vel_obj_retrasada  = vel_obj

        # Acelerar o frenar según velocidad percibida (retrasada)
        if self.velocidad_actual < self._vel_obj_retrasada:
            self.velocidad_actual = min(
                self._vel_obj_retrasada,
                self.velocidad_actual + self.aceleracion * dt,
            )
        else:
            self.velocidad_actual = max(
                self._vel_obj_retrasada,
                self.velocidad_actual - self.frenado * dt,
            )
        self.velocidad_actual = max(0.0, self.velocidad_actual)

        # ── clamp de emergencia en línea de pare ───────────────────────────
        # Ignora tiempo de reacción — es un reflejo, no una decisión.
        # Garantiza que NINGÚN vehículo cruza en rojo por latencia de reacción.
        if estado_semaforo == "ROJO" and not self.ya_cruzo_linea_de_pare():
            if self.frente_progreso() >= self._limite_pare() - 1.0:
                self.velocidad_actual = 0.0

        avance = self.velocidad_actual * dt

        # Clamp de avance: no superar el límite calculado
        if limite is not None:
            avance = max(0.0, min(avance, limite - self.frente_progreso()))

        self.progreso += avance

        # ── clamp de emergencia absoluto contra vehículo de adelante ──────
        # Última línea de defensa física. Nunca se elimina.
        if vehiculo_frente is not None:
            self.progreso = min(
                self.progreso,
                vehiculo_frente.cola_progreso() - DISTANCIA_MINIMA - self._largo() / 2,
            )

        if self.velocidad_actual < 1.0:
            self.tiempo_espera += dt


# ── subclases ──────────────────────────────────────────────────────────────
class Automovil(Vehiculo):
    VELOCIDAD_MAX  = 112.0
    ACELERACION    = 36.0
    FRENADO        = 105.0
    ANCHO, ALTO    = 70, 32
    COLOR_RESPALDO = (255, 215, 0)
    SPRITES        = ["v1.png", "v2.png", "v3.png", "v3.png", "v5.png","v6.png"]

class Moto(Vehiculo):
    VELOCIDAD_MAX  = 130.0
    ACELERACION    = 48.0
    FRENADO        = 115.0
    ANCHO, ALTO    = 35, 16
    COLOR_RESPALDO = (30, 144, 255)
    SPRITES        = ["m1.png", "m2.png", "m3.png"]

class Bus(Vehiculo):
    VELOCIDAD_MAX  = 80.0
    ACELERACION    = 20.0
    FRENADO        = 90.0
    ANCHO, ALTO    = 84, 40
    COLOR_RESPALDO = (186, 85, 211)
    SPRITES        = ["b1.png","b2.png"]

class Camion(Vehiculo):
    VELOCIDAD_MAX  = 85.0
    ACELERACION    = 22.0
    FRENADO        = 88.0
    ANCHO, ALTO    = 90, 38
    COLOR_RESPALDO = (255, 100, 30)
    SPRITES        = ["c1.png", "c2.png", "c3.png", "c4.png"]

TIPOS_VEHICULO = {
    "automovil": Automovil,
    "moto":      Moto,
    "bus":       Bus,
    "camion":    Camion,
}
