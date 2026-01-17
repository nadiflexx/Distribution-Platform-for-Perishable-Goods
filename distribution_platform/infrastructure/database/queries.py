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

GET_PROVINCES_NAME = """
SELECT DISTINCT
    d.nombre AS nombre
FROM dbo.Provincias d;
"""

GET_PROVINCES = """
SELECT * FROM dbo.Provincias;
"""

GET_CLIENTS = """
SELECT * FROM dbo.Clientes;
"""

GET_PRODUCTS = """
SELECT * FROM dbo.Productos;
"""

GET_ORDERS = """
SELECT * FROM dbo.Pedidos;
"""

GET_DESTINATIONS = """
SELECT * FROM dbo.Destinos;
"""

GET_LINE_ITEMS = """
SELECT * FROM dbo.LineasPedido;
"""

GET_FULL_DATA_BY_DATE = """
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
    ON p.DestinoEntregaID = d.DestinoID
WHERE p.FechaPedido >= %(start_date)s AND p.FechaPedido <= %(end_date)s;
"""
