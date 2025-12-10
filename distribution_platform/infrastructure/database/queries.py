GET_FULL_DATA = """
SELECT
    p.PedidoID AS pedido_id,
    p.FechaPedido AS fecha_pedido,
    prod.Nombre AS producto,
    lp.Cantidad AS cantidad_producto,
    prod.PrecioVenta AS precio_venta,
    prod.Caducidad AS caducidad,
    prod.TiempoFabricacionMedio AS tiempo_fabricacion_medio,
    d.nombre_completo AS destino,
    d.distancia_km,
    d.coordenadas_gps,
    c.email AS email_cliente
FROM dbo.LineasPedido lp
LEFT JOIN dbo.Pedidos p 
    ON lp.PedidoID = p.PedidoID
LEFT JOIN dbo.Clientes c 
    ON p.ClienteID = c.ClienteID
LEFT JOIN dbo.Productos prod 
    ON lp.ProductoID = prod.ProductoID
LEFT JOIN dbo.Destinos d 
    ON p.DestinoEntregaID = d.DestinoID;
"""

GET_PROVINCES = """
SELECT DISTINCT
    d.nombre AS nombre
FROM dbo.Provincias d;
"""
