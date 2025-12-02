import math
import networkx as nx
import pandas as pd
from sklearn.cluster import KMeans

# ------------------------------
# UTILIDADES GEOGRÁFICAS
# ------------------------------
def haversine_km(c1, c2):
    R = 6371.0
    lat1, lon1 = map(math.radians, c1)
    lat2, lon2 = map(math.radians, c2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def ruta_dist(G, ruta):
    return round(sum(G[u][v]["weight"] for u,v in zip(ruta, ruta[1:])), 2)

def interp_point(c1, c2, frac):
    """Interpola entre dos coordenadas (aprox lineal)."""
    return (c1[0] + (c2[0]-c1[0])*frac, c1[1] + (c2[1]-c1[1])*frac)

# ------------------------------
# RUTA ÓPTIMA LOCAL (TSP con depósito)
# ------------------------------
def ruta_tsp_local(destinos, depot):
    """Genera ruta mínima DEPOT→...→DEPOT para un grupo de destinos."""
    nodes = [(depot[0], depot[1])] + [(d["lat"], d["lon"]) for d in destinos]
    n = len(nodes)
    G = nx.complete_graph(n)
    for i in range(n):
        for j in range(i+1, n):
            G[i][j]["weight"] = haversine_km(nodes[i], nodes[j])
    ruta = nx.approximation.traveling_salesman_problem(G, cycle=True, weight="weight")
    dist = ruta_dist(G, ruta)
    pedidos = [destinos[i-1]["id"] for i in ruta if i != 0]
    ruta_coords = [nodes[i] for i in ruta]
    return pedidos, ruta_coords, dist

# ------------------------------
# SEGMENTACIÓN POR JORNADAS (≤ Dmax)
# ------------------------------
def segmentar_en_etapas(ruta_coords, vmax_kmh=70, horas_max=8):
    Dmax = vmax_kmh * horas_max
    etapas = []
    etapa_actual = [ruta_coords[0]]
    dist_acum = 0.0
    for i in range(len(ruta_coords)-1):
        a, b = ruta_coords[i], ruta_coords[i+1]
        d = haversine_km(a, b)
        # Si el tramo es muy largo, crear paradas intermedias
        if d > Dmax:
            k = math.ceil(d / Dmax)
            for s in range(1, k+1):
                p = interp_point(a, b, s/k)
                etapa_actual.append(p)
                dist_acum += d/k
                if dist_acum >= Dmax:
                    etapas.append(etapa_actual[:])
                    etapa_actual = [p]
                    dist_acum = 0.0
            continue
        # tramo normal
        if dist_acum + d <= Dmax:
            etapa_actual.append(b)
            dist_acum += d
        else:
            etapas.append(etapa_actual[:])
            etapa_actual = [a, b]
            dist_acum = d
    if len(etapa_actual) > 1:
        etapas.append(etapa_actual)
    return etapas

def km_etapa(coords):
    return round(sum(haversine_km(coords[i], coords[i+1]) for i in range(len(coords)-1)), 2)

# ------------------------------
# PLANIFICACIÓN GLOBAL
# ------------------------------
def planificacion_rutas(destinos, depot, velocidad_kmh=70, horas_max=8, n_clusters=3):
    Dmax = velocidad_kmh * horas_max
    df = pd.DataFrame(destinos)

    # 1️⃣ Agrupar geográficamente
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    df["cluster"] = kmeans.fit_predict(df[["lat", "lon"]])

    plan_camiones = []
    camion_id = 1

    # 2️⃣ Rutas por cluster
    for c in sorted(df["cluster"].unique()):
        subset = df[df["cluster"] == c].to_dict("records")
        pedidos, ruta_coords, dist = ruta_tsp_local(subset, depot)

        # 3️⃣ Si la ruta total excede el límite diario → dividirla
        etapas = segmentar_en_etapas(ruta_coords, velocidad_kmh, horas_max)
        etapas_json = [{"dia": d+1, "km": km_etapa(e), "coords": e} for d,e in enumerate(etapas)]

        plan_camiones.append({
            "camion": camion_id,
            "pedidos": pedidos,
            "dist_total_km": dist,
            "num_dias": len(etapas),
            "etapas": etapas_json
        })
        camion_id += 1

    todos = set(df["id"])
    asignados = set().union(*[set(c["pedidos"]) for c in plan_camiones])
    faltan = sorted(list(todos - asignados))

    return {
        "num_camiones": len(plan_camiones),
        "dist_max_diaria_km": Dmax,
        "camiones": plan_camiones,
        "verificacion": {
            "total_pedidos": len(todos),
            "asignados": len(asignados),
            "faltan_asignar": faltan
        }
    }


# ------------------------------
# EJEMPLO DE USO
# ------------------------------
if __name__ == "__main__":
    depot = (41.5350, 2.4445)  # Mataró
    destinos = [
        {"id": "PED001", "lat": 41.3879, "lon": 2.1699},   # Barcelona
        {"id": "PED002", "lat": 41.9794, "lon": 2.8214},   # Girona
        {"id": "PED003", "lat": 42.1362, "lon": -0.4087},  # Huesca
        {"id": "PED004", "lat": 41.6561, "lon": -0.8773},  # Zaragoza
        {"id": "PED005", "lat": 39.4699, "lon": -0.3763},  # Valencia
        {"id": "PED006", "lat": 40.4168, "lon": -3.7038},  # Madrid
        {"id": "PED007", "lat": 40.2050, "lon": -8.4196},  # Coimbra
        {"id": "PED008", "lat": 38.7169, "lon": -9.1399},  # Lisboa
    ]

    plan = planificacion_rutas(destinos, depot, velocidad_kmh=70, horas_max=8, n_clusters=3)

    print("\n=== PLANIFICACIÓN FINAL ===")
    print("Número de camiones:", plan["num_camiones"])
    print("Límite diario (km):", plan["dist_max_diaria_km"])
    print("Verificación:", plan["verificacion"])

    for c in plan["camiones"]:
        print(f"\nCamión {c['camion']} – {c['dist_total_km']} km en {c['num_dias']} día(s)")
        print("  Pedidos:", c["pedidos"])
        for e in c["etapas"]:
            print(f"   Día {e['dia']} → {e['km']} km")