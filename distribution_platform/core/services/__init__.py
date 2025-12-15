"""
Braincore - Sistema de optimización inteligente de rutas de entrega.

Este módulo integra Machine Learning (K-Means clustering) y algoritmos
genéticos para optimizar rutas de distribución de productos perecederos.

Componentes principales:
- OptimizadorSistema: Interfaz principal de alto nivel
- GestorClustering: Agrupación de pedidos por ML
- GestorGrafo: Cálculo de distancias geográficas
- OptimizadorGenetico: Optimización de rutas individuales
- ConfigCamion, ResultadoRuta: Modelos de datos
"""
from .gestor_clustering import GestorClustering
from .gestor_grafo import GestorGrafo
from .modelos import ConfigCamion, ResultadoRuta
from .optimizador_rutas import OptimizadorGenetico
from .optimizador_sistema import OptimizadorSistema

__all__ = [
    "OptimizadorSistema",
    "GestorClustering",
    "GestorGrafo",
    "OptimizadorGenetico",
    "ConfigCamion",
    "ResultadoRuta",
]
