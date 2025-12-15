"""
Módulo integrador del sistema de optimización de rutas Braincore.

Este módulo proporciona una interfaz de alto nivel para utilizar
el sistema completo de clustering, grafos y optimización genética.
"""
from distribution_platform.core.models.order import Order
from distribution_platform.utils.coordinates_cache import CoordinateCache

from .gestor_clustering import GestorClustering
from .gestor_grafo import GestorGrafo
from .modelos import ConfigCamion, ResultadoRuta
from .optimizador_rutas import OptimizadorGenetico
from .utils_pedidos import consolidar_pedidos


class OptimizadorSistema:
    """
    Clase principal que orquesta todo el sistema de optimización.

    Integra:
    - ETL y carga de pedidos desde CSV/DB
    - CoordinateCache para geolocalización
    - GestorClustering para agrupar pedidos en camiones
    - GestorGrafo para calcular distancias
    - OptimizadorGenetico para optimizar rutas
    """

    def __init__(
        self,
        config_camion: ConfigCamion | None = None,
        origen_base: str = "Mataró",
        coord_cache: CoordinateCache | None = None,
    ):
        """
        Inicializa el sistema de optimización.

        Parameters
        ----------
        config_camion : ConfigCamion, optional
            Configuración del camión. Si no se proporciona, usa valores default.
        origen_base : str, optional
            Ciudad de origen para todas las rutas (default: Mataró).
        coord_cache : CoordinateCache, optional
            Cache de coordenadas. Si no se proporciona, se crea uno nuevo.
        """
        self.config_camion = config_camion if config_camion else ConfigCamion()
        self.origen_base = origen_base
        self.coord_cache = coord_cache if coord_cache else CoordinateCache()

        # Inicializar componentes
        self.gestor_clustering = GestorClustering(coord_cache=self.coord_cache)
        self.gestor_grafo = GestorGrafo(coord_cache=self.coord_cache)

    def optimizar_entregas(
        self,
        pedidos: list[Order] | list[list[Order]],
        n_camiones: int = 2,
        generaciones: int = 200,
        poblacion_tam: int = 50,
        max_pedidos_por_camion: int = 200,
    ) -> dict[int, ResultadoRuta | None]:
        """
        Optimiza las entregas agrupándolas por camiones y calculando rutas óptimas.

        Flujo completo:
        1. Si recibe pedidos agrupados (list[list[Order]]), los consolida
        2. Calcula el número mínimo de camiones necesarios según capacidad
        3. Agrupa pedidos en n_camiones usando ML (K-Means)
        4. Para cada grupo, calcula la ruta óptima con algoritmo genético
        5. Retorna resultados para cada camión

        Parameters
        ----------
        pedidos : list[Order] | list[list[Order]]
            Lista de pedidos a optimizar. Puede ser:
            - list[Order]: pedidos ya consolidados (1 pedido = 1 destino)
            - list[list[Order]]: pedidos agrupados por pedido_id (ETL output)
              Cada sublista son las líneas de productos de un mismo pedido.
              Se consolidarán automáticamente sumando cantidades.
        n_camiones : int, optional
            Número de camiones MÁXIMO disponibles (default: 2).
            El sistema calculará el mínimo necesario.
        generaciones : int, optional
            Generaciones del algoritmo genético (default: 200).
        poblacion_tam : int, optional
            Tamaño de población del algoritmo genético (default: 50).
        max_pedidos_por_camion : int, optional
            Máximo de productos por camión (default: 200). Si un camión tiene más,
            se rechaza para evitar problemas de capacidad y rendimiento.

        Returns
        -------
        dict[int, ResultadoRuta | None]
            Diccionario {camion_id: ResultadoRuta} con las rutas optimizadas.
        """
        if not pedidos:
            print("⚠️ No hay pedidos para optimizar")
            return {}

        # AUTO-CONSOLIDACIÓN: detectar si son pedidos agrupados y consolidar
        if pedidos and isinstance(pedidos[0], list):
            print("🔄 Detectados pedidos agrupados. Consolidando líneas por pedido_id...")
            pedidos_original = len(sum(pedidos, []))  # Total líneas
            pedidos = consolidar_pedidos(pedidos)
            print(f"   ✅ {pedidos_original} líneas → {len(pedidos)} pedidos consolidados\n")

        # FILTRAR DESTINOS IMPOSIBLES (Islas sin conexión terrestre)
        destinos_imposibles = {
            "Las Palmas", "Santa Cruz de Tenerife", "Islas Baleares",
            "Palma de Mallorca", "Ibiza", "Menorca", "Formentera",
            "Tenerife", "Gran Canaria", "Lanzarote", "Fuerteventura",
            "La Palma", "La Gomera", "El Hierro"
        }

        pedidos_entregables = []
        pedidos_no_entregables = []

        print(f"DEBUG: Iniciando filtrado de {len(pedidos)} pedidos")
        
        for pedido in pedidos:
            # Normalizar destino para comparación
            destino_normalizado = pedido.destino.strip()

            # Verificar si el destino está en la lista de imposibles
            es_imposible = any(
                isla.lower() in destino_normalizado.lower()
                for isla in destinos_imposibles
            )

            if es_imposible:
                pedidos_no_entregables.append(pedido)
                print(f"DEBUG: Pedido {pedido.pedido_id} → {destino_normalizado} ES IMPOSIBLE")
            else:
                pedidos_entregables.append(pedido)

        print(f"DEBUG: Resultado filtrado: {len(pedidos_entregables)} entregables, {len(pedidos_no_entregables)} imposibles")
        
        # Guardar pedidos no entregables para devolverlos al final
        self._pedidos_no_entregables = pedidos_no_entregables

        # Mostrar advertencia si hay pedidos no entregables
        if pedidos_no_entregables:
            print(f"\n⚠️ ADVERTENCIA: {len(pedidos_no_entregables)} pedidos a destinos INACCESIBLES por carretera:")
            for pedido in pedidos_no_entregables:
                print(f"   ❌ Pedido {pedido.pedido_id} → {pedido.destino} (isla sin conexión terrestre)")
            print(f"\n   ℹ️ Estos pedidos requieren transporte marítimo o aéreo.\n")

        # Si no hay pedidos entregables, retornar con info de no entregables
        if not pedidos_entregables:
            print("❌ No hay pedidos entregables por carretera")
            return {"pedidos_no_entregables": pedidos_no_entregables}

        # Continuar con pedidos entregables
        pedidos = pedidos_entregables

        # Calcular peso total (cantidad * peso_unitario)
        peso_total = sum(
            pedido.cantidad_producto * self.config_camion.peso_unitario_default
            for pedido in pedidos
        )
        capacidad_por_camion = self.config_camion.capacidad_carga

        # Calcular número MÍNIMO de camiones necesarios por PESO
        import math
        n_camiones_minimo = math.ceil(peso_total / capacidad_por_camion)

        # Asegurar al menos 1 camión
        n_camiones_minimo = max(1, n_camiones_minimo)

        print("\n📦 ANÁLISIS DE CARGA:")
        print(f"   Total pedidos: {len(pedidos)}")
        print(f"   Peso total: {peso_total:.2f} kg")
        print(f"   Capacidad por camión: {capacidad_por_camion:.2f} kg")
        print(f"   Camiones mínimos necesarios: {n_camiones_minimo}")

        # SIEMPRE usar el mínimo calculado para maximizar aprovechamiento
        n_camiones = n_camiones_minimo
        print(f"   ✅ Usando {n_camiones} camion(es)\n")

        # 1. Clustering: Agrupar pedidos en camiones
        print(f"🧠 Agrupando {len(pedidos)} pedidos en {n_camiones} camion(es)...")
        grupos_camiones = self.gestor_clustering.agrupar_pedidos(
            pedidos,
            n_camiones,
            peso_unitario=self.config_camion.peso_unitario_default,
            capacidad_maxima=capacidad_por_camion
        )

        if not grupos_camiones:
            print("❌ No se pudieron agrupar los pedidos")
            return {}

        # 2. Generar matriz de distancias
        print("📊 Generando matriz de distancias...")
        matriz_distancias = self.gestor_grafo.generar_matriz_distancias()

        # 3. Optimizar ruta para cada camión
        resultados: dict[int, ResultadoRuta | None] = {}
        # CAMBIO: Pasamos self.gestor_grafo al constructor para coordenadas
        optimizador = OptimizadorGenetico(
            matriz_distancias,
            self.config_camion,
            self.origen_base,
            gestor_grafo=self.gestor_grafo,
        )

        for camion_id, lista_pedidos in grupos_camiones.items():
            if not lista_pedidos:
                print(f"⚠️ Camión {camion_id + 1}: Sin pedidos asignados")
                resultados[camion_id] = None
                continue

            # Calcular peso total en este camión
            peso_camion = sum(
                pedido.cantidad_producto * self.config_camion.peso_unitario_default
                for pedido in lista_pedidos
            )
            porcentaje_ocupacion = (peso_camion / self.config_camion.capacidad_carga) * 100

            # Validar que no exceda capacidad
            if peso_camion > self.config_camion.capacidad_carga:
                print(
                    f"❌ Camión {camion_id + 1}: {peso_camion:.2f} kg "
                    f"excede capacidad ({self.config_camion.capacidad_carga:.2f} kg)"
                )
                resultados[camion_id] = None
                continue

            print(
                f"\n🚚 CAMIÓN {camion_id + 1}:"
            )
            print(
                f"   Pedidos: {len(lista_pedidos)} | "
                f"Peso: {peso_camion:.2f} kg | "
                f"Ocupación: {porcentaje_ocupacion:.1f}%"
            )
            resultado = optimizador.optimizar(
                lista_pedidos, generaciones, poblacion_tam
            )

            if resultado:
                # Asignar ID de camión
                resultado.camion_id = camion_id + 1
                resultados[camion_id] = resultado

                # Agrupar ciudades únicas con conteo
                from collections import Counter
                ciudad_counts = Counter(resultado.ciudades_ordenadas)
                ruta_resumida = " → ".join(
                    [f"{ciudad} ({count})" if count > 1 else ciudad
                     for ciudad, count in ciudad_counts.items()]
                )

                # Mostrar resumen
                print(f"   ✅ Ruta: {ruta_resumida}")
                print(
                    f"   📏 Distancia: {resultado.distancia_total_km} km | "
                    f"⏱️ Tiempo: {resultado.tiempo_total_viaje_horas} h"
                )
                print(
                    f"   ⛽ Consumo: {resultado.consumo_litros} L | "
                    f"💰 Coste: {resultado.coste_total_ruta} €"
                )
                if not resultado.valida:
                    print("   ⚠️ ATENCIÓN: Ruta excede límites de capacidad/tiempo")
            else:
                resultados[camion_id] = None
                print(f"   ❌ No se pudo optimizar ruta para Camión {camion_id + 1}")

        # Mostrar resumen de aprovechamiento de flota
        print("\n" + "="*70)
        print("📊 RESUMEN DE APROVECHAMIENTO DE FLOTA")
        print("="*70)

        total_productos_transportados = 0
        capacidad_total_disponible = 0

        for camion_id, resultado in resultados.items():
            if resultado:
                peso_en_camion = sum(
                    p.cantidad_producto * self.config_camion.peso_unitario_default
                    for p in resultado.lista_pedidos_ordenada
                )
                total_productos_transportados += peso_en_camion
                capacidad_total_disponible += self.config_camion.capacidad_carga
                ocupacion = (peso_en_camion / self.config_camion.capacidad_carga) * 100
                print(f"🚛 Camión {camion_id + 1}: {peso_en_camion:.1f}/{self.config_camion.capacidad_carga:.1f} kg ({ocupacion:.1f}% ocupación)")

        aprovechamiento_global = (total_productos_transportados / capacidad_total_disponible) * 100 if capacidad_total_disponible > 0 else 0
        print(f"\n✅ Aprovechamiento global de la flota: {aprovechamiento_global:.1f}%")
        print(f"📦 Total peso transportado: {total_productos_transportados:.1f} kg")
        print(f"🚛 Capacidad total disponible: {capacidad_total_disponible:.1f} kg")
        print("="*70 + "\n")

        # Añadir pedidos no entregables al resultado si existen
        if hasattr(self, '_pedidos_no_entregables') and self._pedidos_no_entregables:
            resultados["pedidos_no_entregables"] = self._pedidos_no_entregables
            print(f"DEBUG OPTIMIZADOR: Añadiendo {len(self._pedidos_no_entregables)} pedidos no entregables al resultado")

        return resultados

    def obtener_estadisticas_globales(
        self, resultados: dict[int, ResultadoRuta | None]
    ) -> dict:
        """
        Calcula estadísticas globales del sistema de optimización.

        Parameters
        ----------
        resultados : dict[int, ResultadoRuta | None]
            Resultados de optimización por camión.

        Returns
        -------
        dict
            Diccionario con estadísticas globales incluyendo costes.
        """
        total_euros = 0.0
        total_km = 0.0
        total_horas_conduccion = 0.0
        total_pedidos = 0
        rutas_validas = 0

        for resultado in resultados.values():
            if resultado:
                total_euros += resultado.coste_total_ruta
                total_km += resultado.distancia_total_km
                total_horas_conduccion += resultado.tiempo_conduccion_pura_horas
                total_pedidos += len(resultado.lista_pedidos_ordenada)
                if resultado.valida:
                    rutas_validas += 1

        return {
            "coste_total_flota": round(total_euros, 2),
            "km_totales": round(total_km, 2),
            "horas_conduccion_pagadas": round(total_horas_conduccion, 2),
            "camiones_usados": len(resultados),
            "rutas_validas": rutas_validas,
            "total_pedidos": total_pedidos,
        }
