import pulp
import pandas as pd

# ======================================================
# MODELO 1: ILP que MINIMIZA camiones y DEVUELVE asignación
# ======================================================

def calcular_camiones_y_asignaciones(pedidos_df, capacidad, velocidad, fecha_actual):
    """
    pedidos_df columnas mínimas:
      - id (si no, se crea)
      - cantidad
      - distancia  (Mataró -> destino)
      - fecha_limite (Timestamp)
    """
    df = pedidos_df.copy()

    # Asegura ID único si no existe
    if "id" not in df.columns:
        df["id"] = [f"PID_{i}" for i in range(len(df))]

    n = len(df)
    max_camiones = n

    model = pulp.LpProblem("Calculo_Camiones", pulp.LpMinimize)
    # variables
    x = pulp.LpVariable.dicts('x', (range(n), range(max_camiones)), cat='Binary')
    y = pulp.LpVariable.dicts('y', range(max_camiones), cat='Binary')

    # asignación única
    for i in range(n):
        model += pulp.lpSum(x[i][j] for j in range(max_camiones)) == 1

    # capacidad
    for j in range(max_camiones):
        model += pulp.lpSum(df.iloc[i].cantidad * x[i][j] for i in range(n)) <= capacidad * y[j]

    # caducidad: si no llega a tiempo, ese pedido queda prohibido (inviable)
    for i in range(n):
        tiempo_entrega_dias = df.iloc[i].distancia / velocidad  # ojo: velocidad en km/día
        dias_disp = (df.iloc[i].fecha_limite - fecha_actual).days
        if tiempo_entrega_dias > dias_disp:
            # No se puede asignar a ningún camión
            model += pulp.lpSum(x[i][j] for j in range(max_camiones)) == 0

    # objetivo: minimizar camiones
    model += pulp.lpSum(y[j] for j in range(max_camiones))
    model.solve(pulp.PULP_CBC_CMD(msg=False))

    # camiones usados + asignaciones exactas desde el ILP
    usados = [j for j in range(max_camiones) if pulp.value(y[j]) == 1]

    asignaciones = {}
    for j in usados:
        pedidos_asignados = []
        for i in range(n):
            if pulp.value(x[i][j]) == 1:
                pedidos_asignados.append(df.iloc[i].id)
        # solo si tiene pedidos
        if pedidos_asignados:
            asignaciones[j + 1] = pedidos_asignados  # id de camión desde 1

    return len(usados), asignaciones

if __name__ == "__main__":
    # Ejemplo de datos de pedidos
    data = {
        'cantidad': [10, 20, 15, 30],
        'distancia': [100, 200, 150, 300],
        'fecha_limite': [pd.Timestamp('2024-06-10'), pd.Timestamp('2024-06-12'),
                         pd.Timestamp('2024-06-11'), pd.Timestamp('2024-06-15')]
    }
    pedidos = pd.DataFrame(data)
    capacidad_camion = 50
    velocidad_camion = 60  # km por día
    fecha_actual = pd.Timestamp('2024-06-05')

    num_camiones, asignaciones = calcular_camiones_y_asignaciones(pedidos, capacidad_camion, velocidad_camion, fecha_actual)
    print(f"Número mínimo de camiones necesarios: {num_camiones}")
    print("Asignaciones de pedidos a camiones:")
    for camion_id, pedidos_ids in asignaciones.items():
        print(f"  Camión {camion_id}: {pedidos_ids}")