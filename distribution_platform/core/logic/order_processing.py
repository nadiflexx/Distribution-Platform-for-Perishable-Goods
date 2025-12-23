"""
Order Processing Logic.
Helpers for consolidating and filtering orders before optimization.
"""

from distribution_platform.core.models.order import Order


def consolidate_orders(orders_grouped: list[list[Order]]) -> list[Order]:
    """
    Consolidates lists of order lines (same ID) into single Order objects.
    Sum quantities, take earliest deadline.
    """
    consolidated = []

    for group in orders_grouped:
        if not group:
            continue

        base = group[0]

        total_qty = sum(o.cantidad_producto for o in group)
        total_price = sum(float(o.precio_venta) for o in group)
        min_caducidad = min(o.caducidad for o in group)
        max_fab_time = max(o.tiempo_fabricacion_medio for o in group)
        max_total_days = max(o.dias_totales_caducidad for o in group)
        min_final_date = min(o.fecha_caducidad_final for o in group)

        consolidated.append(
            Order(
                pedido_id=base.pedido_id,
                fecha_pedido=base.fecha_pedido,
                producto=f"Pedido_{base.pedido_id}_Consolidado",
                cantidad_producto=total_qty,
                precio_venta=total_price,
                tiempo_fabricacion_medio=max_fab_time,
                caducidad=min_caducidad,
                destino=base.destino,
                distancia_km=base.distancia_km,
                email_cliente=base.email_cliente,
                dias_totales_caducidad=max_total_days,
                fecha_caducidad_final=min_final_date,
            )
        )

    return consolidated
