"""
Utilidades para procesar y consolidar pedidos.

Este módulo proporciona funciones auxiliares para preparar los datos
de pedidos antes de la optimización de rutas.
"""
from distribution_platform.core.models.order import Order


def consolidar_pedidos(orders_grouped: list[list[Order]]) -> list[Order]:
    """
    Consolida pedidos agrupados en pedidos únicos por destino.

    Cada pedido puede tener múltiples líneas (productos diferentes).
    Esta función suma las cantidades de productos de todas las líneas
    para crear UN solo pedido consolidado por pedido_id.

    Parameters
    ----------
    orders_grouped : list[list[Order]]
        Lista de listas de pedidos, donde cada sublista contiene
        las líneas de productos de un mismo pedido_id.

    Returns
    -------
    list[Order]
        Lista de pedidos consolidados, uno por pedido_id.
        La cantidad_producto es la SUMA de todas las líneas.

    Examples
    --------
    >>> # Pedido 1 con 3 líneas (productos diferentes)
    >>> pedido1 = [
    ...     Order(pedido_id=1, cantidad_producto=5, destino="Madrid"),
    ...     Order(pedido_id=1, cantidad_producto=3, destino="Madrid"),
    ...     Order(pedido_id=1, cantidad_producto=2, destino="Madrid"),
    ... ]
    >>> # Resultado: 1 pedido con cantidad_producto=10
    """
    pedidos_consolidados = []

    for grupo in orders_grouped:
        if not grupo:
            continue

        # Tomar el primer pedido como base
        pedido_base = grupo[0]

        # Sumar TODAS las cantidades de productos del mismo pedido
        cantidad_total = sum(order.cantidad_producto for order in grupo)

        # Tomar la caducidad más urgente (menor)
        caducidad_min = min(order.caducidad for order in grupo)

        # Tomar el máximo de dias_totales_caducidad (más restrictivo)
        dias_totales_max = max(order.dias_totales_caducidad for order in grupo)

        # Tomar la fecha de caducidad más cercana (más urgente)
        fecha_cad_min = min(order.fecha_caducidad_final for order in grupo)

        # Crear pedido consolidado
        pedido_consolidado = Order(
            pedido_id=pedido_base.pedido_id,
            fecha_pedido=pedido_base.fecha_pedido,
            producto=f"Pedido_{pedido_base.pedido_id}",  # Nombre genérico
            cantidad_producto=cantidad_total,  # SUMA de todas las líneas
            precio_venta=sum(order.precio_venta for order in grupo),
            tiempo_fabricacion_medio=max(
                order.tiempo_fabricacion_medio for order in grupo
            ),
            caducidad=caducidad_min,  # Más urgente
            destino=pedido_base.destino,
            distancia_km=pedido_base.distancia_km,
            email_cliente=pedido_base.email_cliente,
            dias_totales_caducidad=dias_totales_max,  # Más restrictivo
            fecha_caducidad_final=fecha_cad_min,  # Más urgente
        )

        pedidos_consolidados.append(pedido_consolidado)

    return pedidos_consolidados


def aplanar_pedidos(orders_grouped: list[list[Order]]) -> list[Order]:
    """
    Aplana una lista de listas de pedidos en una lista simple.

    ADVERTENCIA: Esta función NO consolida. Cada línea de producto
    se trata como un pedido separado. Use consolidar_pedidos() en su lugar
    para optimización de rutas.

    Parameters
    ----------
    orders_grouped : list[list[Order]]
        Lista de listas de pedidos.

    Returns
    -------
    list[Order]
        Lista plana de todos los pedidos.
    """
    pedidos_planos = []
    for grupo in orders_grouped:
        pedidos_planos.extend(grupo)
    return pedidos_planos
