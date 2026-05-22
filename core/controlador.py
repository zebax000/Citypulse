class ControladorCruce:
    """
    Ciclo de fases:
    H_VERDE → H_AMARILLO → TODO_ROJO_1 → V_VERDE → V_AMARILLO → TODO_ROJO_2 → H_VERDE
    Nunca H y V en verde simultáneamente. TODO_ROJO garantiza el vaciado de cruce.
    """
    FASES = [
        "HORIZONTAL_VERDE", "HORIZONTAL_AMARILLO",
        "TODO_ROJO_1",
        "VERTICAL_VERDE", "VERTICAL_AMARILLO",
        "TODO_ROJO_2",
    ]

    def __init__(self, verde_h, amarillo_h, verde_v, amarillo_v, todo_rojo=2.0):
        self.todo_rojo = float(todo_rojo)
        self.verde_h = float(verde_h)
        self.amarillo_h = float(amarillo_h)
        self.verde_v = float(verde_v)
        self.amarillo_v = float(amarillo_v)
        self.fase = "HORIZONTAL_VERDE"
        self.timer = 0.0

    def reiniciar(self):
        self.fase = "HORIZONTAL_VERDE"
        self.timer = 0.0

    def actualizar(self, dt):
        self.timer += dt
        duracion = self._duracion_actual()
        while self.timer >= duracion:
            self.timer -= duracion
            idx = self.FASES.index(self.fase)
            self.fase = self.FASES[(idx + 1) % len(self.FASES)]
            duracion = self._duracion_actual()

    def _duracion_actual(self):
        return {
            "HORIZONTAL_VERDE": self.verde_h,
            "HORIZONTAL_AMARILLO": self.amarillo_h,
            "TODO_ROJO_1": self.todo_rojo,
            "VERTICAL_VERDE": self.verde_v,
            "VERTICAL_AMARILLO": self.amarillo_v,
            "TODO_ROJO_2": self.todo_rojo,
        }[self.fase]

    def estado_grupo(self, grupo):
        if grupo == "H":
            if self.fase == "HORIZONTAL_VERDE":    return "VERDE"
            if self.fase == "HORIZONTAL_AMARILLO": return "AMARILLO"
            return "ROJO"
        # grupo == "V"
        if self.fase == "VERTICAL_VERDE":    return "VERDE"
        if self.fase == "VERTICAL_AMARILLO": return "AMARILLO"
        return "ROJO"

    def tiempo_restante_grupo(self, grupo):
        restante_fase = self._duracion_actual() - self.timer
        if grupo == "H":
            if self.fase == "HORIZONTAL_VERDE":    return restante_fase
            if self.fase == "HORIZONTAL_AMARILLO": return restante_fase
            if self.fase == "TODO_ROJO_1":         return restante_fase
            if self.fase == "VERTICAL_VERDE":      return restante_fase + self.amarillo_v + self.todo_rojo
            if self.fase == "VERTICAL_AMARILLO":   return restante_fase + self.todo_rojo
            return restante_fase  # TODO_ROJO_2
        # grupo "V"
        if self.fase == "VERTICAL_VERDE":    return restante_fase
        if self.fase == "VERTICAL_AMARILLO": return restante_fase
        if self.fase == "TODO_ROJO_2":       return restante_fase
        if self.fase == "HORIZONTAL_VERDE":  return restante_fase + self.amarillo_h + self.todo_rojo
        if self.fase == "HORIZONTAL_AMARILLO": return restante_fase + self.todo_rojo
        return restante_fase  # TODO_ROJO_1
