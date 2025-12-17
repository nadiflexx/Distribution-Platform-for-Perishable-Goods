"""
Optimizador de rutas usando Algoritmo Genético.

Este módulo implementa un algoritmo genético para optimizar las rutas
de entrega minimizando distancia, tiempo y costos de combustible,
respetando restricciones de capacidad, caducidad y jornada laboral.
"""

import random

import pandas as pd

from distribution_platform.core.models.order import Order

from .modelos import ConfigCamion, ResultadoRuta


class OptimizadorGenetico:
    """Optimizador de rutas mediante algoritmo genético."""

    def __init__(
        self,
        matriz_distancias: pd.DataFrame,
        config: ConfigCamion,
        origen_base: str = "Mataró",
        gestor_grafo=None,
    ):
        """
        Inicializa el optimizador genético.

        Parameters
        ----------
        matriz_distancias : pd.DataFrame
            Matriz de distancias entre ciudades.
        config : ConfigCamion
            Configuración del camión.
        origen_base : str, optional
            Ciudad de origen (default: Mataró).
        gestor_grafo : GestorGrafo, optional
            Gestor de grafos para obtener coordenadas.
        """
        self.matriz = matriz_distancias
        self.config = config
        self.origen = origen_base
        self.gestor_grafo = gestor_grafo

    def _simular_cronograma(self, distancia_km: float) -> tuple[float, float]:
        """
        Simula el viaje con las reglas estrictas:
        - 2h conducción -> 20min descanso.
        - 8h conducción/día -> 12h descanso.

        Parameters
        ----------
        distancia_km : float
            Distancia del tramo a simular.

        Returns
        -------
        tuple[float, float]
            (tiempo_total_transcurrido, tiempo_conduccion_pagable)
        """
        tiempo_pendiente_conducir = distancia_km / self.config.velocidad_constante

        tiempo_viaje_reloj = 0.0  # El tiempo que pasa en el mundo real
        tiempo_pagable = (
            tiempo_pendiente_conducir  # El conductor cobra por lo que conduce
        )

        # Contadores temporales para la simulación
        conduccion_acumulada_dia = 0.0
        conduccion_acumulada_tramo = 0.0

        while tiempo_pendiente_conducir > 0:
            # Avanzamos en bloques pequeños (ej. 0.1 horas) o lo que falte
            paso = min(tiempo_pendiente_conducir, 0.1)

            tiempo_pendiente_conducir -= paso
            tiempo_viaje_reloj += paso
            conduccion_acumulada_dia += paso
            conduccion_acumulada_tramo += paso

            # 1. Regla: Descanso Corto (cada 2h seguidas)
            if (
                conduccion_acumulada_tramo >= self.config.max_conduccion_seguida
                and tiempo_pendiente_conducir > 0
            ):
                tiempo_viaje_reloj += self.config.tiempo_descanso_corto  # +20 min
                conduccion_acumulada_tramo = 0  # Reinicia contador tramo

            # 2. Regla: Descanso Diario (cada 8h acumuladas en el día)
            if (
                conduccion_acumulada_dia >= self.config.max_conduccion_dia
                and tiempo_pendiente_conducir > 0
            ):
                tiempo_viaje_reloj += self.config.tiempo_descanso_diario  # +12 horas
                conduccion_acumulada_dia = 0  # Nuevo día
                conduccion_acumulada_tramo = 0  # También resetea el tramo continuo

        return tiempo_viaje_reloj, tiempo_pagable

    def _calcular_fitness_ruta(
        self, pedidos_ordenados: list[Order]
    ) -> tuple[float, bool, float, float, float, float, float, float, float]:
        """
        Calcula el fitness de una ruta con simulación realista de costes.

        Parameters
        ----------
        pedidos_ordenados : list[Order]
            Lista ordenada de pedidos a entregar.

        Returns
        -------
        tuple
            (score, es_valida, distancia_km, tiempo_reloj, tiempo_conduccion,
             litros, coste_total, coste_chofer, coste_gasolina)
        """
        distancia_total = 0.0
        tiempo_reloj_total = 0.0
        tiempo_conduccion_total = 0.0
        penalizacion = 0.0
        carga_actual = 0.0
        tiempos_llegada = []  # Tiempos de llegada a cada pedido

        ciudad_actual = self.origen

        # Simulación tramo a tramo
        for p in pedidos_ordenados:
            # Validar que el pedido no sea None
            if p is None:
                penalizacion += 100000
                continue

            # Validar que la ciudad exista en la matriz
            if (
                ciudad_actual not in self.matriz.index
                or p.destino not in self.matriz.columns
            ):
                penalizacion += 50000
                continue

            dist = self.matriz.at[ciudad_actual, p.destino]
            distancia_total += dist

            # Simular tiempos con reglas de descanso
            t_reloj, t_conduccion = self._simular_cronograma(dist)

            tiempo_reloj_total += t_reloj
            tiempo_conduccion_total += t_conduccion

            # Guardar tiempo de llegada para este pedido
            tiempos_llegada.append(tiempo_reloj_total)

            # Validar Caducidad (Usamos tiempo reloj porque el producto envejece)
            # El producto tiene dias_totales_caducidad que incluye fabricación + caducidad
            dias_pasados = tiempo_reloj_total / 24.0

            # Verificar si el producto caduca antes de la entrega
            if hasattr(p, "dias_totales_caducidad"):
                dias_limite = p.dias_totales_caducidad
            else:
                # Fallback: usar solo caducidad del producto
                dias_limite = p.caducidad

            if dias_pasados > dias_limite:
                # Penalización alta: producto caducado antes de entrega
                penalizacion += 10000
                # print(f"   ⚠️ Producto {p.producto} caducaría en ruta (días: {dias_pasados:.1f} > {dias_limite})")

            # Calcular peso (cantidad * peso_unitario)
            carga_actual += p.cantidad_producto * self.config.peso_unitario_default
            ciudad_actual = p.destino

        # Añadir viaje de vuelta al origen (ida y vuelta)
        if ciudad_actual != self.origen and ciudad_actual in self.matriz.index:
            if self.origen in self.matriz.columns:
                dist_vuelta = self.matriz.at[ciudad_actual, self.origen]
                distancia_total += dist_vuelta

                # Simular tiempo de vuelta
                t_reloj_vuelta, t_conduccion_vuelta = self._simular_cronograma(
                    dist_vuelta
                )
                tiempo_reloj_total += t_reloj_vuelta
                tiempo_conduccion_total += t_conduccion_vuelta

        # Validar capacidad: ahora es número total de productos
        if carga_actual > self.config.capacidad_carga:
            penalizacion += 10000

        # Costes Económicos
        coste_chofer = tiempo_conduccion_total * self.config.salario_conductor_hora
        litros = (distancia_total / 100) * self.config.consumo_combustible
        coste_gasolina = litros * self.config.precio_combustible_litro

        coste_total = coste_chofer + coste_gasolina

        # El Score es el Dinero + Penalizaciones (Queremos minimizar esto)
        score = coste_total + penalizacion

        return (
            score,
            (penalizacion == 0),
            distancia_total,
            tiempo_reloj_total,
            tiempo_conduccion_total,
            litros,
            coste_total,
            coste_chofer,
            coste_gasolina,
            tiempos_llegada,  # Nuevos tiempos de llegada
        )

    def optimizar(
        self,
        lista_pedidos: list[Order],
        generaciones: int = 200,
        poblacion_tam: int = 50,
    ) -> ResultadoRuta | None:
        """
        Optimiza la ruta de entrega usando algoritmo genético.

        Parameters
        ----------
        lista_pedidos : list[Order]
            Lista de pedidos a optimizar.
        generaciones : int, optional
            Número de generaciones del algoritmo genético (default: 200).
        poblacion_tam : int, optional
            Tamaño de la población (default: 50).

        Returns
        -------
        ResultadoRuta | None
            Resultado optimizado o None si no hay pedidos.
        """
        if not lista_pedidos:
            return None

        # Filtrar pedidos None por si acaso
        lista_pedidos = [p for p in lista_pedidos if p is not None]

        if not lista_pedidos:
            return None

        # Si solo hay 1-2 pedidos, no necesitamos algoritmo genético
        # Usar solución directa (greedy) es más rápido
        if len(lista_pedidos) <= 2:
            # Calcular fitness directamente
            fit_res = self._calcular_fitness_ruta(lista_pedidos)
            (
                _,
                valida,
                dist,
                t_reloj,
                t_cond,
                litros,
                c_total,
                c_chof,
                c_gas,
                t_llegadas,
            ) = fit_res

            # Incluir origen al principio y al final (ida y vuelta)
            ciudades = (
                [self.origen] + [p.destino for p in lista_pedidos] + [self.origen]
            )

            # Recuperar coordenadas (incluye vuelta al origen)
            coords_ruta: list[tuple[float, float]] = []
            if self.gestor_grafo:
                lat_o, lon_o = self.gestor_grafo.obtener_coordenadas(self.origen)
                if lat_o is not None and lon_o is not None:
                    coords_ruta.append((lat_o, lon_o))
                for p in lista_pedidos:
                    lat, lon = self.gestor_grafo.obtener_coordenadas(p.destino)
                    if lat is not None and lon is not None:
                        coords_ruta.append((lat, lon))
                # Añadir coordenadas del origen al final (vuelta)
                if lat_o is not None and lon_o is not None:
                    coords_ruta.append((lat_o, lon_o))

            # Determinar mensaje
            if valida:
                mensaje = "✅ Ruta Óptima - Todos los productos se entregan a tiempo"
            else:
                tiempo_dias = t_reloj / 24.0
                problemas = []

                for p in lista_pedidos:
                    dias_limite = getattr(p, "dias_totales_caducidad", p.caducidad)
                    if tiempo_dias > dias_limite:
                        problemas.append("⚠️ Productos podrían caducar")
                        break

                peso_total = sum(
                    p.cantidad_producto * self.config.peso_unitario_default
                    for p in lista_pedidos
                )
                if peso_total > self.config.capacidad_carga:
                    problemas.append(
                        f"⚠️ Excede capacidad: {peso_total:.1f} kg > {self.config.capacidad_carga:.1f} kg"
                    )

                mensaje = (
                    " | ".join(problemas) if problemas else "⚠️ Restricciones Violadas"
                )

            # Calcular ingresos y beneficios
            ingresos = sum(p.precio_venta for p in lista_pedidos)
            beneficio = ingresos - c_total

            return ResultadoRuta(
                camion_id=0,
                lista_pedidos_ordenada=lista_pedidos,
                ciudades_ordenadas=ciudades,
                ruta_coordenadas=coords_ruta,
                tiempos_llegada=[round(t, 2) for t in t_llegadas],
                distancia_total_km=round(dist, 2),
                tiempo_total_viaje_horas=round(t_reloj, 2),
                tiempo_conduccion_pura_horas=round(t_cond, 2),
                consumo_litros=round(litros, 2),
                coste_combustible=round(c_gas, 2),
                coste_conductor=round(c_chof, 2),
                coste_total_ruta=round(c_total, 2),
                ingresos_totales=round(ingresos, 2),
                beneficio_neto=round(beneficio, 2),
                valida=valida,
                mensaje=mensaje,
            )

        # --- Algoritmo Genético ---
        # OPTIMIZACIÓN: Ajustar parámetros según tamaño de ruta
        n_pedidos = len(lista_pedidos)

        # Ajustar generaciones: menos pedidos = menos generaciones necesarias
        if n_pedidos <= 5:
            generaciones = min(generaciones, 30)  # Rutas pequeñas: 30 gen
        elif n_pedidos <= 10:
            generaciones = min(generaciones, 75)  # Rutas medianas: 75 gen
        else:
            generaciones = min(generaciones, 150)  # Rutas grandes: 150 gen max

        poblacion_tam = min(poblacion_tam, n_pedidos * 3)  # Ajustar tamaño de población

        # 1. Población Inicial: Listas de pedidos barajadas
        poblacion = [
            random.sample(lista_pedidos, len(lista_pedidos))
            for _ in range(poblacion_tam)
        ]
        mejor_ruta_pack = None
        mejor_score = float("inf")
        generaciones_sin_mejora = 0
        max_sin_mejora = 10  # Early stopping: parar si no mejora en 10 gen

        for gen in range(generaciones):
            # Evaluar
            scores = []
            mejor_en_esta_gen = False
            for indiv in poblacion:
                # Desempaquetamos los 9 valores que devuelve ahora la función
                fit_res = self._calcular_fitness_ruta(indiv)
                score = fit_res[0]
                scores.append((score, indiv, fit_res))

                if score < mejor_score:
                    mejor_score = score
                    mejor_ruta_pack = (indiv, fit_res)
                    mejor_en_esta_gen = True

            # Actualizar contador de early stopping
            if mejor_en_esta_gen:
                generaciones_sin_mejora = 0
            else:
                generaciones_sin_mejora += 1

            # Early stopping: si no hay mejora en N generaciones, terminar
            if generaciones_sin_mejora >= max_sin_mejora:
                # print(f"   ⏱️ Early stopping en generación {gen+1}/{generaciones}")
                break

            # Selección (Torneo simple o ordenar)
            scores.sort(key=lambda x: x[0])  # Ordenar por menor score
            seleccionados = [x[1] for x in scores[: int(poblacion_tam / 2)]]  # Top 50%

            # Cruce y Mutación para rellenar población
            nueva_poblacion = seleccionados.copy()
            while len(nueva_poblacion) < poblacion_tam:
                # Verificar que hay al menos 2 elementos para muestrear
                if len(seleccionados) >= 2:
                    p1, p2 = random.sample(seleccionados, 2)
                    hijo = self._cruce_ox(p1, p2)
                    if random.random() < 0.2:
                        self._mutacion_swap(hijo)
                    nueva_poblacion.append(hijo)
                else:
                    # Si solo hay 1 elemento, duplicarlo con mutación
                    if seleccionados:
                        hijo = seleccionados[0].copy()
                        if len(hijo) >= 2:
                            self._mutacion_swap(hijo)
                        nueva_poblacion.append(hijo)
                    else:
                        break
            poblacion = nueva_poblacion

        # Empaquetar Resultado
        if not mejor_ruta_pack:
            return None

        # Construir Resultado Final
        pedidos_final = mejor_ruta_pack[0]
        # fit_res: score, valida, dist, t_reloj, t_cond, litros, coste_tot, coste_chof, coste_gas, tiempos_llegada
        (
            _,
            valida,
            dist,
            t_reloj,
            t_cond,
            litros,
            c_total,
            c_chof,
            c_gas,
            t_llegadas,
        ) = mejor_ruta_pack[1]

        # Incluir origen al principio y al final (ida y vuelta)
        ciudades = [self.origen] + [p.destino for p in pedidos_final] + [self.origen]

        # Recuperar Coordenadas para el Front (incluye vuelta al origen)
        coords_ruta: list[tuple[float, float]] = []
        if self.gestor_grafo:
            lat_o, lon_o = self.gestor_grafo.obtener_coordenadas(self.origen)
            if lat_o is not None and lon_o is not None:
                coords_ruta.append((lat_o, lon_o))
            for p in pedidos_final:
                lat, lon = self.gestor_grafo.obtener_coordenadas(p.destino)
                if lat is not None and lon is not None:
                    coords_ruta.append((lat, lon))
            # Añadir coordenadas del origen al final (vuelta)
            if lat_o is not None and lon_o is not None:
                coords_ruta.append((lat_o, lon_o))

        # Determinar mensaje más específico
        if valida:
            mensaje = "✅ Ruta Óptima - Todos los productos se entregan a tiempo"
        else:
            # Verificar qué restricción se violó
            tiempo_dias = t_reloj / 24.0
            problemas = []

            # Verificar caducidad
            for p in pedidos_final:
                dias_limite = getattr(p, "dias_totales_caducidad", p.caducidad)
                if tiempo_dias > dias_limite:
                    problemas.append("⚠️ Productos podrían caducar")
                    break

            # Verificar capacidad (peso en kg)
            peso_total = sum(
                p.cantidad_producto * self.config.peso_unitario_default
                for p in pedidos_final
            )
            if peso_total > self.config.capacidad_carga:
                problemas.append(
                    f"⚠️ Excede capacidad: {peso_total:.1f} kg > {self.config.capacidad_carga:.1f} kg"
                )

            mensaje = " | ".join(problemas) if problemas else "⚠️ Restricciones Violadas"

        # Calcular ingresos y beneficios
        ingresos = sum(p.precio_venta for p in pedidos_final)
        beneficio = ingresos - c_total

        return ResultadoRuta(
            camion_id=0,  # Se asigna fuera
            lista_pedidos_ordenada=pedidos_final,
            ciudades_ordenadas=ciudades,
            ruta_coordenadas=coords_ruta,  # Lista de (lat, lon) para pintar
            tiempos_llegada=[round(t, 2) for t in t_llegadas],
            distancia_total_km=round(dist, 2),
            tiempo_total_viaje_horas=round(t_reloj, 2),
            tiempo_conduccion_pura_horas=round(t_cond, 2),
            consumo_litros=round(litros, 2),
            coste_combustible=round(c_gas, 2),
            coste_conductor=round(c_chof, 2),
            coste_total_ruta=round(c_total, 2),
            ingresos_totales=round(ingresos, 2),
            beneficio_neto=round(beneficio, 2),
            valida=valida,
            mensaje=mensaje,
        )

    # Operadores Genéticos Auxiliares (Standard TSP)
    def _cruce_ox(self, p1: list[Order], p2: list[Order]) -> list[Order]:
        """Operador de cruce Order Crossover (OX)."""
        size = len(p1)
        if size == 0:
            return []
        if size == 1:
            return p1.copy()

        a, b = sorted(random.sample(range(size), 2))
        hijo: list[Order | None] = [None] * size
        hijo[a:b] = p1[a:b]
        pos = b
        for item in p2:
            if item not in p1[a:b]:
                if pos >= size:
                    pos = 0
                hijo[pos] = item
                pos += 1

        # Verificar que no haya None (seguridad adicional)
        if None in hijo:
            # Si hay None, devolver una copia del padre
            return p1.copy()

        return hijo  # type: ignore

    def _mutacion_swap(self, ruta: list[Order]) -> None:
        """Operador de mutación por intercambio."""
        if len(ruta) < 2:
            return  # No se puede mutar una ruta con menos de 2 elementos
        idx1, idx2 = random.sample(range(len(ruta)), 2)
        ruta[idx1], ruta[idx2] = ruta[idx2], ruta[idx1]
