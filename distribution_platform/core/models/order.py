from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class Order(BaseModel):
    """
    Represents an order for a perishable good.

    Attributes
    ----------
        pedido_id (int): Unique identifier for the order.
        fecha_pedido (Union[date, str]): Date of the order in YYYY-MM-DD format.
        producto (str): Name of the product.
        cantidad_producto (int): Quantity of the product.
        precio_venta (Union[float, str]): Sale price of the product
         (may use comma as decimal separator).
        tiempo_fabricacion_medio (int): Average manufacturing time in hours.
        caducidad (int): Expiry in days.
        destino (str): Destination address.
        distancia_km (Union[float, str]): Distance in kilometers.
        coordenadas_gps (str): GPS coordinates in 'latitud,longitud' format.
        email_cliente (EmailStr): Customer's email address.
    """

    # Unique identifier for the order
    pedido_id: int = Field(description="Unique identifier for the order")

    # Date of the order (YYYY-MM-DD format)
    fecha_pedido: date | str = Field(description="Order date in YYYY-MM-DD format")

    # Name of the product
    producto: str = Field(description="Name of the product")
    # Quantity of the product
    cantidad_producto: int = Field(description="Quantity of the product")

    # Sale price (may use comma as decimal separator)
    precio_venta: float | str = Field(
        description="Product price (may use comma as decimal separator)"
    )

    # Average manufacturing time in hours
    tiempo_fabricacion_medio: int = Field(
        description="Average manufacturing time in hours"
    )

    # Expiry in days
    caducidad: int = Field(description="Expiry in days")

    # Destination address
    destino: str
    # Distance in kilometers
    distancia_km: float | str = Field(description="Distance in kilometers")
    # GPS coordinates in 'latitud,longitud' format
    # coordenadas_gps: str | None

    # Customer's email address
    email_cliente: EmailStr = Field(description="Customer's email address")
    dias_totales_caducidad: int = Field(
        description="Total caducity days (1 + fabrication time + caducity)"
    )
    fecha_caducidad_final: date | str = Field(description="Final expiry date")
    # -------------------------------------------
    # VALIDATORS
    # -------------------------------------------

    @field_validator("precio_venta", "distancia_km")
    def clean_decimals(cls, v):
        """
        Converts European-style numbers '45,84' to float 45.84.
        If already a float or int, returns as float.
        """
        if isinstance(v, (int, float)):
            return float(v)
        # Replace comma with dot for decimal conversion
        return float(v.replace(",", "."))

    @field_validator("fecha_pedido")
    def validate_date(cls, v):
        """
        Validates and converts the date string to a date object.
        Accepts date object or string in YYYY-MM-DD format.
        """
        if isinstance(v, date):
            return v
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except Exception as err:
            raise ValueError("Date must be in YYYY-MM-DD format") from err

    @field_validator("fecha_caducidad_final")
    def validate_fecha_cad_final(cls, v):
        if isinstance(v, date):
            return v
        return datetime.strptime(v, "%Y-%m-%d").date()
