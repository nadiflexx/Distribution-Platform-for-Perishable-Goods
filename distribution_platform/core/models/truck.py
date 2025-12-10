from pydantic import BaseModel


class Truck(BaseModel):
    """Modelo de camión final después de validación."""

    nombre: str
    velocidad_constante: float
    consumo_combustible: float
    capacidad_carga: float
    precio_conductor_hora: float  # €/h
    imagen: str  # nombre de archivo
