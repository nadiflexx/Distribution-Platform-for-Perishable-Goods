from pydantic import BaseModel, field_validator


class Truck(BaseModel):
    velocidad_constante: bool
    consumo_combustible: float  # in liters per 100 km
    limite_consumo: float  # acceptable limit in liters per 100 km
    capacidad_carga: float  # in kg
    carga_requerida: float  # in kg

    @field_validator("consumo_combustible")
    def check_consumo_combustible(cls, value, values):
        if value > values.get("limite_consumo", float("inf")):
            raise ValueError("Consumo de combustible excede el límite aceptable")
        return value

    @field_validator("capacidad_carga")
    def check_capacidad_carga(cls, value, values):
        if value < values.get("carga_requerida", 0):
            raise ValueError("Capacidad de carga insuficiente para la carga requerida")
        return value
