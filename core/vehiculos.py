# core/vehiculos.py
import os
import math
import random

try:
    import pygame
    _PYGAME_DISPONIBLE = True
except ImportError:
    _PYGAME_DISPONIBLE = False

DISTANCIA_SEGURIDAD = 22
DISTANCIA_MINIMA    = 4
ESPACIO_SPAWN       = 110

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
                img    = pygame.transform.scale(img, (ancho, alto))
                angulo = -90 if direccion > 0 else 90
                img    = pygame.transform.rotate(img, angulo)
            return img
        except Exception:
            pass
    w    = ancho if eje == "x" else alto
    h    = alto  if eje == "x" else ancho
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill(color_respaldo)
    pygame.draw.rect(surf, (20, 20, 20), surf.get_rect(), 2, border_radius=4)
    return surf.convert_alpha()


class Vehiculo:
    VELOCIDAD_MAX    = 100.0
    ACELERACION      = 30.0
    FRENADO          = 100.0
    ANCHO            = 60
    ALTO             = 30
    COLOR_RESPALDO   = (200, 200, 200)
    SPRITES          = []
    ES_PRIORITARIO   = False
    ANGULO_MAX_VISUAL = 10.0   # grados máximos de inclinación durante lane change
    FACTOR_VEL_LATERAL = 1.0   # multiplicador de velocidad lateral (subclases lo reducen)

    def __init__(self, id_v, carril):
        self.id     = id_v
        self.carril = carril
        self.ancho  = self.ANCHO
        self.alto   = self.ALTO
        self.color  = self.COLOR_RESPALDO

        self.agresividad         = random.uniform(0.25, 0.90)
        self.tiempo_reaccion     = random.uniform(0.06, 0.20)
        self.suavidad_frenado    = random.uniform(0.60, 1.00)
        self.tolerancia_amarillo = random.uniform(0.15, 0.65)

        self._reaccion_acum     = 0.0
        self._vel_obj_retrasada = 0.0

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
        self.frenado = self.FRENADO * max(0.75, 1.15 - self.suavidad_frenado * 0.40)

        self.velocidad_actual   = random.uniform(
            self.velocidad_max * 0.40,
            self.velocidad_max * 0.65,
        )
        self._vel_obj_retrasada = self.velocidad_actual
        self.progreso           = -self._largo()
        self.tiempo_espera      = 0.0

        # FSM lane change — cambio lógico INMEDIATO + interpolación visual
        self._estado_cambio     = "LIBRE"
        self._intencion_vecino  = None
        self._carril_destino    = None
        self._timer_intencion   = 0.0
        self._cooldown_cambio   = random.uniform(2.0, 5.0)
        self._intentos_fallidos = {}
        self._signo_visual_cambio = 0.0

        self._offset_lateral = 0.0
        self.offset_lateral  = 0.0

        # magnitud inicial del offset para normalizar la interpolación del ángulo
        self._offset_inicial   = 0.0

        # ── ángulo visual — SOLO para render, no afecta física ni colisiones ──
        # 0.0 = sin inclinación
        # positivo = gira hacia abajo/derecha
        # negativo = gira hacia arriba/izquierda
        self.angulo_visual = 0.0

        self._cediendo_paso   = False
        self._cooldown_cesion = 0.0
        self._decision_cruce  = None   # None | "CRUZAR" | "DETENER"

        # Fase E: posición lateral dentro del carril (inactivo hasta Fase E)
        self.posicion_lateral = 0.0

        self.image = None
        if _PYGAME_DISPONIBLE:
            sprite     = _elegir_sprite(self.SPRITES)
            self.image = _cargar_imagen(
                sprite, self.ancho, self.alto,
                carril.eje, carril.direccion, self.COLOR_RESPALDO,
            )

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

    def puede_entrar_a_cruce(self):
        """
        Restricción física de box blocking.
        Retorna False solo si el espacio después del cruce está
        genuinamente ocupado por un vehículo detenido o muy lento.
        Vehículos en movimiento no bloquean — se proyecta su posición.
        """
        carril = self.carril

        distancia_al_pare = self._limite_pare() - self.frente_progreso()
        if distancia_al_pare > 50 or distancia_al_pare < 0:
            return True

        largo_propio = self._largo() + DISTANCIA_MINIMA * 2

        vehiculos_salida = [
            v for v in carril.vehiculos
            if v is not self
            and v.progreso > carril.progreso_pare
            and v._estado_cambio != "CAMBIANDO"
        ]

        if not vehiculos_salida:
            return True

        mas_cercano = min(vehiculos_salida, key=lambda v: v.progreso)

        # proyectar posición en ~0.5s — si se está moviendo, habrá espacio
        tiempo_llegada  = max(0.1, distancia_al_pare / max(1.0, self.velocidad_actual))
        proyeccion      = mas_cercano.cola_progreso() + mas_cercano.velocidad_actual * min(tiempo_llegada, 1.0)
        espacio_real    = proyeccion - carril.progreso_pare

        return espacio_real >= largo_propio

    def _limite_pare(self):
        pp = self._progreso_pare_activo()
        if pp is None:
            return float("inf")
        return pp - self.carril.margen_detencion

    def salio_del_mapa(self):
        return self.cola_progreso() > self.carril.longitud_total

    def posicion_px(self):
        return self.carril.posicion_mundo(self.progreso)

    def _distancia_seguridad(self):
        por_velocidad    = self.velocidad_actual * 0.08
        por_personalidad = (1.0 - self.agresividad) * 8.0
        return max(DISTANCIA_SEGURIDAD * 0.5,
                   DISTANCIA_SEGURIDAD + por_velocidad + por_personalidad)

    def _prioritario_detras(self, radio=220):
        mi_cola   = self.cola_progreso()
        candidato = None
        dist_min  = radio
        for otro in self.carril.vehiculos:
            if otro is self:
                continue
            if not getattr(otro, "ES_PRIORITARIO", False):
                continue
            dist = mi_cola - otro.frente_progreso()
            if 0 < dist < dist_min:
                dist_min  = dist
                candidato = otro
        return candidato

    def _ceder_paso_si_necesario(self, dt):
        if self._cooldown_cesion > 0:
            self._cooldown_cesion -= dt
            if self._cooldown_cesion <= 0:
                self._cediendo_paso = False   # reset al expirar cooldown
            return

        for vecino in self.carril.vecinos:
            for otro in vecino.vehiculos:
                if getattr(otro, "_estado_cambio", "LIBRE") != "PREPARANDO":
                    continue
                if getattr(otro, "_intencion_vecino", None) is not self.carril:
                    continue
                if abs(otro.progreso - self.progreso) > 80:
                    continue
                prob_cesion = 0.65 - self.agresividad * 0.45
                if random.random() < prob_cesion:
                    self._cediendo_paso   = True
                    self._cooldown_cesion = random.uniform(1.5, 3.0)
                return
        if self._cediendo_paso:
            self._cediendo_paso = False

    def _hueco_seguro_en(self, carril_destino, posicion_lateral_destino: float = 0.0):
        mi_frente = self.frente_progreso()
        mi_cola   = self.cola_progreso()
        margen    = self._distancia_seguridad()
        for otro in carril_destino.vehiculos:
            if otro is self:
                continue
            if (otro.cola_progreso() < mi_frente + margen and
                    otro.frente_progreso() > mi_cola - margen):
                return False
        return True

    def _hueco_minimo_en(self, carril_destino):
        mi_frente = self.frente_progreso()
        mi_cola   = self.cola_progreso()
        margen    = DISTANCIA_MINIMA * 4
        for otro in carril_destino.vehiculos:
            if otro is self:
                continue
            if (otro.cola_progreso() < mi_frente + margen and
                    otro.frente_progreso() > mi_cola - margen):
                return False
        return True

    def _conviene_cambiar(self, carril_destino, vehiculo_frente):
        prioritario        = self._prioritario_detras()
        presion_emergencia = prioritario is not None

        if not presion_emergencia:
            if vehiculo_frente is None:
                return False
            if (self.velocidad_actual - vehiculo_frente.velocidad_actual
                    < self.velocidad_max * 0.20):
                return False

        pp = self._progreso_pare_activo()
        if pp is not None and (pp - self.frente_progreso()) < 150:
            return False

        congestion_destino = carril_destino.nivel_congestion()
        congestion_actual  = self.carril.nivel_congestion()

        if not presion_emergencia:
            if congestion_destino >= congestion_actual:
                return False
            if (congestion_actual - congestion_destino) < 0.15:
                return False

        if presion_emergencia:
            umbral = 0.30 + self.agresividad * 0.55
        else:
            umbral = self.agresividad * 0.55 * (
                1.0 + congestion_actual - congestion_destino
            )
        return random.random() <= umbral

    def intentar_cambio_carril(self, vehiculo_frente):
        if self._cooldown_cambio > 0 or self._estado_cambio != "LIBRE":
            return
        for vecino in self.carril.vecinos:
            if getattr(vecino, "bloqueado_accidente", False):
                continue   # no cambiar a carril con accidente
            if not self._conviene_cambiar(vecino, vehiculo_frente):
                continue
            if not self._hueco_seguro_en(vecino):
                continue
            cruce = any(
                getattr(otro, "_estado_cambio", "LIBRE") in ("PREPARANDO", "CAMBIANDO")
                and getattr(otro, "_intencion_vecino", None) is self.carril
                for otro in vecino.vehiculos
                if abs(otro.progreso - self.progreso) < self._largo() * 3
            )
            if cruce:
                continue
            self._estado_cambio    = "PREPARANDO"
            self._intencion_vecino = vecino
            self._timer_intencion  = max(
                0.06,
                random.uniform(0.08, 0.25) * (1.5 - self.agresividad)
            )
            break

    def _ejecutar_cambio_si_listo(self, dt):
        if self._estado_cambio != "PREPARANDO":
            return
        self._timer_intencion -= dt
        if self._timer_intencion > 0:
            return
        vecino = self._intencion_vecino
        if vecino is None or vecino not in self.carril.vecinos:
            self._abortar_cambio(cooldown=1.0)
            return
        competidores = [
            otro for otro in self.carril.vehiculos
            if otro is not self
            and getattr(otro, "_estado_cambio", "LIBRE") == "CAMBIANDO"
            and getattr(otro, "_carril_destino", None) is vecino
            and abs(otro.progreso - self.progreso) < self._largo() * 2
        ]
        if competidores:
            self._abortar_cambio(cooldown=random.uniform(0.3, 0.8))
            return
        if self._hueco_minimo_en(vecino):
            delta = self.carril.coordenada_fija - vecino.coordenada_fija
            if self in self.carril.vehiculos:
                self.carril.vehiculos.remove(self)
            vecino.vehiculos.append(self)
            self._carril_destino   = vecino
            self.carril            = vecino
            self._offset_lateral   = float(delta)
            self.offset_lateral    = float(delta)
            self._offset_inicial   = float(delta)

            self._estado_cambio = "CAMBIANDO"

            if delta == 0:
                self._signo_visual_cambio = 0.0
            else:
                signo_base = (
                        (1.0 if delta > 0 else -1.0)
                        * self.carril.direccion
                )

                # SOLO eje X necesita inversión
                if self.carril.eje == "x":
                    signo_base *= -1.0

                self._signo_visual_cambio = signo_base

        else:
            clave = id(vecino)
            self._intentos_fallidos[clave] = self._intentos_fallidos.get(clave, 0) + 1
            backoff = min(4.0, 0.8 * (1.4 ** self._intentos_fallidos[clave]))
            self._abortar_cambio(cooldown=backoff)

    def _vel_lateral(self):
        """
        Velocidad lateral en px/s para la animación del lane change.
        Target: ~0.6s–1.2s para un delta típico de 40–60px.
        Vehículos agresivos más rápidos. Subclases pesadas reducen con FACTOR_VEL_LATERAL.
        """
        base = 28.0 + self.agresividad * 22.0   # rango base: 28–50 px/s
        return base * self.FACTOR_VEL_LATERAL

    def _actualizar_animacion_lateral(self, dt):
        if self._estado_cambio != "CAMBIANDO":
            # Fuera de CAMBIANDO: devolver ángulo a 0 suavemente
            if self.angulo_visual != 0.0:
                paso_ang = 120.0 * dt
                if abs(self.angulo_visual) <= paso_ang:
                    self.angulo_visual = 0.0
                elif self.angulo_visual > 0:
                    self.angulo_visual -= paso_ang
                else:
                    self.angulo_visual += paso_ang
            return

        vel_lateral = self._vel_lateral()
        paso        = vel_lateral * dt

        if abs(self._offset_lateral) <= paso:
            self._offset_lateral = 0.0
        elif self._offset_lateral > 0:
            self._offset_lateral -= paso
        else:
            self._offset_lateral += paso

        self.offset_lateral = self._offset_lateral

        # ── ángulo visual basado en progreso del cambio ───────────────────
        # progreso 0.0 = inicio (offset = offset_inicial)
        # progreso 1.0 = fin   (offset = 0)
        # curva: seno para arrancar en 0°, pico a mitad, volver a 0°
        if self._offset_inicial != 0.0:
            t = 1.0 - abs(self._offset_lateral) / abs(self._offset_inicial)
            t = max(0.0, min(1.0, t))
            # sin(pi*t): 0 → 1 → 0 a lo largo del cambio
            factor_seno    = math.sin(math.pi * t)

            angulo_objetivo = (
                    self.ANGULO_MAX_VISUAL
                    * factor_seno
                    * self._signo_visual_cambio
            )
        else:
            angulo_objetivo = 0.0

        # Suavizado del ángulo visual — no saltar directamente al objetivo
        paso_ang = 180.0 * dt   # 180°/s máximo de cambio angular
        diff     = angulo_objetivo - self.angulo_visual
        if abs(diff) <= paso_ang:
            self.angulo_visual = angulo_objetivo
        elif diff > 0:
            self.angulo_visual += paso_ang
        else:
            self.angulo_visual -= paso_ang

        # Convergencia garantizada al llegar a offset 0
        if self._offset_lateral == 0.0:
            self._estado_cambio    = "LIBRE"
            self._intencion_vecino = None
            self._carril_destino   = None
            self._offset_inicial   = 0.0
            # angulo_visual se devuelve a 0 en el siguiente frame por el bloque de arriba

    def _abortar_cambio(self, cooldown=1.5):
        self._estado_cambio    = "LIBRE"
        self._intencion_vecino = None
        self._carril_destino   = None
        self._signo_visual_cambio = 0.0
        self._offset_lateral   = 0.0
        self.offset_lateral    = 0.0
        self._offset_inicial   = 0.0
        self.angulo_visual     = 0.0
        self._cooldown_cambio  = cooldown

    def _velocidad_objetivo(self, vehiculo_frente, estado_semaforo):
        objetivo = self.velocidad_max
        limite   = None

        # ── lógica de semáforo con decisión binaria ────────────────────────
        if not self.ya_cruzo_linea_de_pare():

            if estado_semaforo == "ROJO":
                # siempre detenerse
                self._decision_cruce = "DETENER"

            elif estado_semaforo == "AMARILLO":
                # tomar decisión UNA sola vez al entrar en zona amarilla
                if self._decision_cruce is None:
                    distancia = self._limite_pare() - self.frente_progreso()
                    puede_cruzar = (
                        distancia <= 55
                        or self.tolerancia_amarillo >= 0.45
                    )
                    self._decision_cruce = "CRUZAR" if puede_cruzar else "DETENER"

            else:
                # VERDE — sin restricción
                self._decision_cruce = None

            # aplicar decisión
            if self._decision_cruce == "DETENER":
                limite = self._limite_pare()

        # ── seguidor de vehículo delante ───────────────────────────────────
        if vehiculo_frente is not None and vehiculo_frente.carril is self.carril:
            limite_v = vehiculo_frente.cola_progreso() - self._distancia_seguridad()
            limite   = min(limite, limite_v) if limite is not None else limite_v

        # ── velocidad objetivo basada en límite ────────────────────────────
        if limite is not None:
            distancia = limite - self.frente_progreso()
            if distancia <= 0:
                return 0.0, limite
            objetivo = min(
                objetivo,
                math.sqrt(max(0.0, 2.0 * self.frenado * distancia))
            )

        return objetivo, limite

    def actualizar(self, dt, vehiculo_frente, estado_semaforo):
        if self._cooldown_cambio > 0:
            self._cooldown_cambio -= dt
        # reset decisión de cruce si ya pasó la línea o semáforo está verde
        if self.ya_cruzo_linea_de_pare():
            self._decision_cruce = None

        self._ejecutar_cambio_si_listo(dt)
        self._actualizar_animacion_lateral(dt)
        self._ceder_paso_si_necesario(dt)

        # ── box blocking prevention — solo activo cerca del cruce ─────────
        estado_efectivo = estado_semaforo

        vel_obj, limite = self._velocidad_objetivo(vehiculo_frente, estado_efectivo)

        if self._cediendo_paso:
            vel_obj = min(vel_obj, self.velocidad_max * 0.65)

        self._reaccion_acum += dt
        if self._reaccion_acum >= self.tiempo_reaccion:
            self._reaccion_acum     = 0.0
            self._vel_obj_retrasada = vel_obj

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

        # clamp físico final — solo si realmente sobrepasó el límite en DETENER
        if (self._decision_cruce == "DETENER"
                and not self.ya_cruzo_linea_de_pare()
                and self.frente_progreso() >= self._limite_pare()):
            self.velocidad_actual = max(
                0.0, self.velocidad_actual - self.frenado * dt * 3
            )

        avance = self.velocidad_actual * dt
        if limite is not None:
            avance = max(0.0, min(avance, limite - self.frente_progreso()))
        self.progreso += avance

        if limite is not None and self.frente_progreso() > limite:
            self.progreso = limite - self._largo() / 2

        if vehiculo_frente is not None and vehiculo_frente.carril is self.carril:
            self.progreso = min(
                self.progreso,
                vehiculo_frente.cola_progreso() - DISTANCIA_MINIMA - self._largo() / 2,
            )

        if self.velocidad_actual < 1.0:
            self.tiempo_espera += dt


class VehiculoPrioritario(Vehiculo):
    VELOCIDAD_MAX      = 130.0
    ACELERACION        = 50.0
    FRENADO            = 120.0
    ANCHO, ALTO        = 72, 34
    COLOR_RESPALDO     = (255, 50, 50)
    SPRITES            = []
    ES_PRIORITARIO     = True
    ANGULO_MAX_VISUAL  = 7.0    # giran menos — van rápido, angulo reducido
    FACTOR_VEL_LATERAL = 1.2    # cambian de carril más rápido

    def __init__(self, id_v, carril):
        super().__init__(id_v, carril)
        self.agresividad         = 0.95
        self.tiempo_reaccion     = 0.03
        self.suavidad_frenado    = 0.75
        self.tolerancia_amarillo = 0.90
        self.velocidad_max       = self.VELOCIDAD_MAX * 1.05
        self.aceleracion         = self.ACELERACION
        self.frenado             = self.FRENADO
        self._vel_obj_retrasada  = self.velocidad_max * 0.60
        self._cooldown_cambio    = 0.5

    def _conviene_cambiar(self, carril_destino, vehiculo_frente):
        pp = self._progreso_pare_activo()
        if pp is not None and (pp - self.frente_progreso()) < 120:
            return False
        if carril_destino.nivel_congestion() >= self.carril.nivel_congestion() - 0.10:
            return False
        return random.random() <= 0.75


class Ambulancia(VehiculoPrioritario):
    COLOR_RESPALDO = (255, 255, 255)
    SPRITES        = ["a1.png", "a2.png"]


class Policia(VehiculoPrioritario):
    COLOR_RESPALDO = (30, 80, 255)
    SPRITES        = ["p1.png", "p2.png"]


class Automovil(Vehiculo):
    VELOCIDAD_MAX      = 112.0
    ACELERACION        = 36.0
    FRENADO            = 105.0
    ANCHO, ALTO        = 70, 32
    COLOR_RESPALDO     = (255, 215, 0)
    SPRITES            = ["v1.png", "v2.png", "v3.png", "v5.png", "v6.png"]
    ANGULO_MAX_VISUAL  = 10.0
    FACTOR_VEL_LATERAL = 1.0


class Moto(Vehiculo):
    VELOCIDAD_MAX      = 130.0
    ACELERACION        = 48.0
    FRENADO            = 115.0
    ANCHO, ALTO        = 35, 16
    COLOR_RESPALDO     = (30, 144, 255)
    SPRITES            = ["m1.png", "m2.png", "m3.png"]
    ANGULO_MAX_VISUAL  = 14.0   # motos se inclinan más
    FACTOR_VEL_LATERAL = 1.15   # ágiles
    ancho_logico       = 12

    def _hueco_seguro_en(self, carril_destino, posicion_lateral_destino: float = 0.0):
        congestion         = carril_destino.nivel_congestion()
        velocidad_max_dest = max(
            (v.velocidad_actual for v in carril_destino.vehiculos), default=0
        )
        filtrando = velocidad_max_dest < 15.0 and congestion > 0.50
        mi_frente = self.frente_progreso()
        mi_cola   = self.cola_progreso()
        margen    = self.ancho_logico if filtrando else self._distancia_seguridad()
        for otro in carril_destino.vehiculos:
            if otro is self:
                continue
            if (otro.cola_progreso() < mi_frente + margen and
                    otro.frente_progreso() > mi_cola - margen):
                return False
        return True


class Bus(Vehiculo):
    VELOCIDAD_MAX      = 80.0
    ACELERACION        = 20.0
    FRENADO            = 90.0
    ANCHO, ALTO        = 84, 40
    COLOR_RESPALDO     = (186, 85, 211)
    SPRITES            = ["b1.png", "b2.png"]
    ANGULO_MAX_VISUAL  = 6.0    # buses se inclinan poco
    FACTOR_VEL_LATERAL = 0.65   # lentos y pesados


class Camion(Vehiculo):
    VELOCIDAD_MAX      = 85.0
    ACELERACION        = 22.0
    FRENADO            = 88.0
    ANCHO, ALTO        = 90, 38
    COLOR_RESPALDO     = (255, 100, 30)
    SPRITES            = ["c1.png", "c2.png", "c3.png", "c4.png"]
    ANGULO_MAX_VISUAL  = 5.0    # camiones muy poco
    FACTOR_VEL_LATERAL = 0.55   # los más lentos lateralmente


TIPOS_VEHICULO = {
    "automovil":  Automovil,
    "moto":       Moto,
    "bus":        Bus,
    "camion":     Camion,
    "ambulancia": Ambulancia,
    "policia":    Policia,
}
