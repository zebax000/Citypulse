# core/controlador.py

class ControladorCruce:
    """
    Ciclo: H_VERDE → H_AMARILLO → TODO_ROJO_1 → V_VERDE → V_AMARILLO → TODO_ROJO_2
    Nunca H y V en verde simultáneamente.
    """
    FASES = [
        "HORIZONTAL_VERDE", "HORIZONTAL_AMARILLO",
        "TODO_ROJO_1",
        "VERTICAL_VERDE", "VERTICAL_AMARILLO",
        "TODO_ROJO_2",
    ]

    def __init__(self, verde_h, amarillo_h, verde_v, amarillo_v, todo_rojo=2.0):
        self.todo_rojo  = float(todo_rojo)
        self.verde_h    = float(verde_h)
        self.amarillo_h = float(amarillo_h)
        self.verde_v    = float(verde_v)
        self.amarillo_v = float(amarillo_v)
        self.fase       = "HORIZONTAL_VERDE"
        self.timer      = 0.0
        self._carriles  = None

    def reiniciar(self):
        self.fase  = "HORIZONTAL_VERDE"
        self.timer = 0.0

    def actualizar(self, dt):
        self.timer += dt
        duracion = self._duracion_actual()
        while self.timer >= duracion:
            self.timer -= duracion
            idx      = self.FASES.index(self.fase)
            siguiente = self.FASES[(idx + 1) % len(self.FASES)]
            if siguiente in ("HORIZONTAL_VERDE", "VERTICAL_VERDE"):
                grupo = "H" if siguiente == "HORIZONTAL_VERDE" else "V"
                if self._salida_bloqueada(grupo):
                    self.timer = -1.5
            self.fase = siguiente
            duracion  = self._duracion_actual()

    def _salida_bloqueada(self, grupo):
        if self._carriles is None:
            return False
        return any(
            c.nivel_congestion() >= 0.95
            for c in self._carriles
            if c.grupo_semaforo == grupo
        )

    def _duracion_actual(self):
        return {
            "HORIZONTAL_VERDE":    self.verde_h,
            "HORIZONTAL_AMARILLO": self.amarillo_h,
            "TODO_ROJO_1":         self.todo_rojo,
            "VERTICAL_VERDE":      self.verde_v,
            "VERTICAL_AMARILLO":   self.amarillo_v,
            "TODO_ROJO_2":         self.todo_rojo,
        }[self.fase]

    def estado_grupo(self, grupo):
        if grupo == "H":
            if self.fase == "HORIZONTAL_VERDE":    return "VERDE"
            if self.fase == "HORIZONTAL_AMARILLO": return "AMARILLO"
            return "ROJO"
        if self.fase == "VERTICAL_VERDE":    return "VERDE"
        if self.fase == "VERTICAL_AMARILLO": return "AMARILLO"
        return "ROJO"

    def tiempo_restante_grupo(self, grupo):
        restante = self._duracion_actual() - self.timer
        if grupo == "H":
            if self.fase == "HORIZONTAL_VERDE":    return restante
            if self.fase == "HORIZONTAL_AMARILLO": return restante
            if self.fase == "TODO_ROJO_1":         return restante
            if self.fase == "VERTICAL_VERDE":      return restante + self.amarillo_v + self.todo_rojo
            if self.fase == "VERTICAL_AMARILLO":   return restante + self.todo_rojo
            return restante

        if self.fase == "VERTICAL_VERDE":      return restante
        if self.fase == "VERTICAL_AMARILLO":   return restante
        if self.fase == "TODO_ROJO_2":         return restante
        if self.fase == "HORIZONTAL_VERDE":    return restante + self.amarillo_h + self.todo_rojo
        if self.fase == "HORIZONTAL_AMARILLO": return restante + self.todo_rojo
        return restante
