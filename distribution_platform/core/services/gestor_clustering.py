"""
Gestor de clustering para agrupar pedidos usando Machine Learning.

Este módulo utiliza K-Means para agrupar pedidos por ubicación geográfica
y urgencia de entrega basada en la caducidad del producto.
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from distribution_platform.core.models.order import Order
from distribution_platform.utils.coordinates_cache import CoordinateCache


class GestorClustering:
    """Gestor de clustering para agrupar pedidos en camiones."""

    def __init__(self, coord_cache: CoordinateCache | None = None):
        """
        Inicializa el gestor de clustering.

        Parameters
        ----------
        coord_cache : CoordinateCache, optional
            Cache de coordenadas para enriquecer pedidos con lat/lon.
        """
        self.scaler = StandardScaler()
        self.coord_cache = coord_cache if coord_cache else CoordinateCache()

    def _enriquecer_coordenadas(self, pedidos: list[Order]) -> list[dict]:
        """
        Enriquece pedidos con coordenadas desde el cache.

        Parameters
        ----------
        pedidos : list[Order]
            Lista de pedidos a enriquecer.

        Returns
        -------
        list[dict]
            Lista de diccionarios con lat, lon y urgencia.
        """
        data_matrix = []
        for p in pedidos:
            # Obtener coordenadas del cache
            coord_str = self.coord_cache.get(p.destino)
            if coord_str is None:
                print(f"⚠️ Advertencia: No hay coordenadas para destino '{p.destino}'")
                continue

            try:
                lat_str, lon_str = coord_str.split(",")
                lat = float(lat_str)
                lon = float(lon_str)
            except (ValueError, AttributeError):
                print(f"⚠️ Formato incorrecto de coordenadas para '{p.destino}'")
                continue

            # Calcular urgencia: menor caducidad = mayor urgencia
            # Reducimos el peso para priorizar agrupación geográfica (rutas más eficientes)
            # Factor más bajo = más importancia a la ubicación geográfica
            factor_urgencia = (1.0 / (p.caducidad + 1)) * 50
            data_matrix.append(
                {"pedido": p, "lat": lat, "lon": lon, "urgencia": factor_urgencia}
            )

        return data_matrix

    def agrupar_pedidos(
        self,
        pedidos: list[Order],
        n_camiones: int,
        peso_unitario: float = 1.0,
        capacidad_maxima: float = 1000.0,
    ) -> dict[int, list[Order]]:
        """
        Agrupa pedidos en n_camiones usando K-Means y balanceo por PESO.

        Parameters
        ----------
        pedidos : list[Order]
            Lista de pedidos a agrupar.
        n_camiones : int
            Número de camiones (clusters) deseados.
        peso_unitario : float, optional
            Peso por unidad de producto (default: 1.0 kg).
        capacidad_maxima : float, optional
            Capacidad máxima de carga por camión en kg (default: 1000.0).

        Returns
        -------
        dict[int, list[Order]]
            Diccionario {camion_id: [lista_pedidos]}.
        """
        if not pedidos:
            return {}

        # 1. Enriquecer con coordenadas
        data_enriched = self._enriquecer_coordenadas(pedidos)
        if not data_enriched:
            print("❌ No se pudieron obtener coordenadas para ningún pedido")
            return {}

        # 2. Preparar datos para ML (Lat, Lon, Urgencia)
        df = pd.DataFrame(
            [
                {
                    "lat": item["lat"],
                    "lon": item["lon"],
                    "urgencia": item["urgencia"],
                }
                for item in data_enriched
            ]
        )

        # 3. Normalizar (vital para K-Means)
        datos_escalados = self.scaler.fit_transform(df)

        # 4. K-Means
        kmeans = KMeans(n_clusters=n_camiones, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(datos_escalados)

        # 5. Reconstruir respuesta inicial
        resultado: dict[int, list[Order]] = {i: [] for i in range(n_camiones)}
        for idx, cluster_id in enumerate(clusters):
            resultado[cluster_id].append(data_enriched[idx]["pedido"])

        # 6. Balancear clusters por PESO (no por cantidad)
        resultado = self._balancear_clusters_por_peso(
            resultado, peso_unitario, capacidad_maxima, n_camiones
        )

        return resultado

    def _balancear_clusters_por_peso(
        self,
        clusters: dict[int, list[Order]],
        peso_unitario: float,
        capacidad_maxima: float,
        n_camiones: int,
    ) -> dict[int, list[Order]]:
        """
        Re-balancea clusters que excedan la capacidad máxima de PESO.
        Itera hasta que todos los clusters estén dentro del límite de peso.

        Parameters
        ----------
        clusters : dict[int, list[Order]]
            Clusters iniciales.
        peso_unitario : float
            Peso por unidad de producto (kg).
        capacidad_maxima : float
            Capacidad máxima de carga por camión en kg.
        n_camiones : int
            Número total de camiones.

        Returns
        -------
        dict[int, list[Order]]
            Clusters balanceados por peso.
        """

        def calcular_peso_total(orders):
            """Calcula el peso total de una lista de pedidos."""
            return sum(order.cantidad_producto * peso_unitario for order in orders)

        # Pre-cachear pesos de pedidos para evitar recálculos
        peso_cache = {}
        for _, orders in clusters.items():
            for order in orders:
                if id(order) not in peso_cache:
                    peso_cache[id(order)] = order.cantidad_producto * peso_unitario

        def calcular_peso_total_cache(orders):
            """Calcula peso total usando cache."""
            return sum(peso_cache[id(order)] for order in orders)

        max_iteraciones = 5  # Reducido drasticamente para performance
        iteracion = 0
        redistribuciones = 0

        while iteracion < max_iteraciones:
            # Identificar clusters sobrecargados por PESO
            sobrecargados = [
                (k, v)
                for k, v in clusters.items()
                if calcular_peso_total_cache(v) > capacidad_maxima
            ]

            if not sobrecargados:
                # Todos los clusters están balanceados
                break

            if iteracion == 0:
                print(
                    f"   ⚙️ Balanceando {len(sobrecargados)} clusters sobrecargados por peso..."
                )

            # Limitar redistribuciones por iteración para evitar loops infinitos
            max_redistribuciones_por_iter = 10
            redistribuciones_iter = 0

            # Redistribuir pedidos excedentes
            for cluster_id, _ in sobrecargados:
                if redistribuciones_iter >= max_redistribuciones_por_iter:
                    break

                # Sacar solo UN pedido pesado por iteración
                if not clusters[cluster_id]:
                    continue

                peso_actual = calcular_peso_total_cache(clusters[cluster_id])
                if peso_actual <= capacidad_maxima:
                    continue

                # Sacar el pedido más pesado del cluster sobrecargado
                pedido_mas_pesado = max(
                    clusters[cluster_id],
                    key=lambda p: peso_cache[id(p)],
                )
                clusters[cluster_id].remove(pedido_mas_pesado)
                redistribuciones += 1
                redistribuciones_iter += 1

                peso_pedido = peso_cache[id(pedido_mas_pesado)]

                # Buscar cluster con espacio suficiente
                clusters_con_espacio = [
                    k
                    for k in clusters
                    if calcular_peso_total_cache(clusters[k]) + peso_pedido
                    <= capacidad_maxima
                ]

                if clusters_con_espacio:
                    # Asignar al cluster con más espacio libre
                    cluster_destino = min(
                        clusters_con_espacio,
                        key=lambda k: calcular_peso_total_cache(clusters[k]),
                    )
                    clusters[cluster_destino].append(pedido_mas_pesado)
                else:
                    # Si no hay espacio, asignar al menos cargado
                    cluster_destino = min(
                        clusters.keys(),
                        key=lambda k: calcular_peso_total_cache(clusters[k]),
                    )
                    clusters[cluster_destino].append(pedido_mas_pesado)

            iteracion += 1

        # PASO FINAL: Verificar si quedan sobrecargas y crear camiones adicionales
        clusters_sobrecargados = [
            (k, v)
            for k, v in clusters.items()
            if calcular_peso_total_cache(v) > capacidad_maxima
        ]

        if clusters_sobrecargados:
            print(
                f"   ⚠️ {len(clusters_sobrecargados)} camiones aún sobrecargados. Añadiendo camiones adicionales..."
            )
            # Encontrar el siguiente ID disponible
            next_id = max(clusters.keys()) + 1

            for cluster_id, _ in clusters_sobrecargados:
                while (
                    calcular_peso_total_cache(clusters[cluster_id]) > capacidad_maxima
                ):
                    if not clusters[cluster_id]:
                        break

                    # Extraer el pedido más pesado
                    pedido = max(clusters[cluster_id], key=lambda p: peso_cache[id(p)])
                    peso_pedido = peso_cache[id(pedido)]

                    # Si un solo pedido pesa más que la capacidad, no se puede hacer nada
                    if (
                        peso_pedido > capacidad_maxima
                        and len(clusters[cluster_id]) == 1
                    ):
                        print(
                            f"   ⚠️ Camión {cluster_id + 1}: Pedido único de {peso_pedido:.2f} kg excede capacidad"
                        )
                        break

                    clusters[cluster_id].remove(pedido)

                    # Buscar un camión existente con espacio
                    camion_con_espacio = None
                    for k in clusters:
                        if (
                            calcular_peso_total_cache(clusters[k]) + peso_pedido
                            <= capacidad_maxima
                        ):
                            camion_con_espacio = k
                            break

                    if camion_con_espacio is not None:
                        clusters[camion_con_espacio].append(pedido)
                    else:
                        # Crear nuevo camión
                        clusters[next_id] = [pedido]
                        next_id += 1

        # Verificar y mostrar resultado final
        print(f"   ✓ Redistribuciones realizadas: {redistribuciones}")
        print(f"   ✓ Distribución final: {len(clusters)} camiones")
        for k, v in clusters.items():
            peso = calcular_peso_total_cache(v)
            porcentaje = (peso / capacidad_maxima) * 100
            estado = "✅" if peso <= capacidad_maxima else "⚠️"
            print(
                f"      {estado} Camión {k + 1}: {len(v)} pedidos, "
                f"{peso:.2f} kg ({porcentaje:.1f}% capacidad)"
            )

        return clusters
