import math
import networkx as nx
import pandas as pd
import numpy as np

## ======================================================
# AUX: Distancias y TSP (NetworkX + 2-opt)
# ======================================================

def haversine_km(coord1, coord2):
    R = 6371
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon / 2)**2
    return 2 * R * math.asin(math.sqrt(a))

def total_distance(route, dist_matrix):
    return sum(dist_matrix[route[i], route[i + 1]] for i in range(len(route) - 1))

def two_opt(route, dist_matrix):
    best = route
    improved = True
    best_distance = total_distance(route, dist_matrix)
    while improved:
        improved = False
        for i in range(1, len(route) - 2):
            for j in range(i + 1, len(route)):
                if j - i == 1:
                    continue
                new_route = route[:]
                new_route[i:j] = route[j - 1:i - 1:-1]
                new_distance = total_distance(new_route, dist_matrix)
                if new_distance < best_distance:
                    best = new_route
                    best_distance = new_distance
                    improved = True
        route = best
    return best, best_distance

def calcular_ruta_optima(depot, destinos):
    """
    destinos: lista de dicts con claves: id, lat, lon
    """
    nodos = [("DEPOT", depot[0], depot[1])] + [(d["id"], d["lat"], d["lon"]) for d in destinos]
    n = len(nodos)

    # matriz de distancias
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_matrix[i, j] = haversine_km(
                    (nodos[i][1], nodos[i][2]),
                    (nodos[j][1], nodos[j][2])
                )

    # grafo completo ponderado
    G = nx.complete_graph(n)
    for i in range(n):
        for j in range(i + 1, n):
            G[i][j]["weight"] = dist_matrix[i, j]

    # TSP aproximado + 2-opt
    ruta_ini = nx.approximation.traveling_salesman_problem(G, cycle=True, weight="weight")
    ruta, dist = two_opt(ruta_ini, dist_matrix)

    ruta_ids = [nodos[i][0] for i in ruta]
    ruta_coords = [(nodos[i][1], nodos[i][2]) for i in ruta]

    return {
        "ruta_ids": ruta_ids,
        "ruta_coords": ruta_coords,
        "distancia_total_km": round(dist, 2),
    }

# ------------------------------
# EJEMPLO DE USO
# ------------------------------

if __name__ == "__main__":
    # Coordenadas del depósito (Mataró)
    depot = (41.5350, 2.4445)

    # Lista de destinos simulados
    destinos = [
        {"id": "PED001", "lat": 41.3879, "lon": 2.1699},   # Barcelona
        {"id": "PED002", "lat": 41.9794, "lon": 2.8214},   # Girona
        {"id": "PED003", "lat": 42.1362, "lon": -0.4087},  # Huesca
        {"id": "PED004", "lat": 41.6561, "lon": -0.8773},  # Zaragoza
    ]

    resultado = calcular_ruta_optima(depot, destinos)

    print("Ruta óptima (orden de visitas):", " → ".join(resultado["ruta_ids"]))
    print("Distancia total estimada (km):", resultado["distancia_total_km"])