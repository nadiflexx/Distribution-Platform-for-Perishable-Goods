from pydantic import BaseModel


class Truck(BaseModel):
    """Truck final model after validation.

       Attributes
    ----------
        nombre: "Name of the truck"
        velocidad_constante: "Average speed km/h"
        consumo_combustible: "Liters per 100km"
        capacidad_carga: "Max load in kg or units"
        precio_conductor_hora: "Driver price €/h"
        imagen: "Image of the truck"
    """

    nombre: str
    velocidad_constante: float
    consumo_combustible: float
    capacidad_carga: float
    precio_conductor_hora: float
    imagen: str
