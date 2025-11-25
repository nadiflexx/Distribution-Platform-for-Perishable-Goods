import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from distribution_platform.utils import data_loaders
from distribution_platform.utils import data_cleaning
from distribution_platform.utils import enums
from distribution_platform.pipelines.preprocessing_pipeline import run_preprocessing
from distribution_platform.utils.helper import get_coordinates
from distribution_platform.config import paths
def run():

    #Load datasets 
    df_clientes = data_loaders.load_data(enums.DataTypesEnum.CSV,  paths.DATA_RAW / "dboClientes.csv")
    df_lineas_pedido = data_loaders.load_data(enums.DataTypesEnum.CSV,  paths.DATA_RAW / "dboLineasPedido.csv")
    df_pedidos = data_loaders.load_data(enums.DataTypesEnum.CSV,  paths.DATA_RAW / "dboPedidos.csv")
    df_productos = data_loaders.load_data(enums.DataTypesEnum.CSV,  paths.DATA_RAW / "dboProductos.csv")
    df_provincias = data_loaders.load_data(enums.DataTypesEnum.CSV, paths.DATA_RAW / "dboProvincias.csv")
    df_destinos = data_loaders.load_data(enums.DataTypesEnum.CSV, paths.DATA_RAW / "dboDestinos.csv")



    #Clean datasets

    if os.path.exists(paths.DATA_PROCESSED / "pedidos.csv"):
        return data_loaders.load_data(enums.DataTypesEnum.CSV, paths.DATA_PROCESSED / "pedidos.csv")
    else:
        df_destinos["coordenadas_gps"] = df_destinos["nombre_completo"].apply(get_coordinates)

        #Merge destinos + provincias
        df_pedidos = df_pedidos.rename(columns={"DestinoEntregaID":"DestinoID"}, errors="raise")
        df_destinos = df_destinos.drop(columns="provinciaID")

        df_clientes = data_cleaning.to_snake_case(df_clientes)
        df_lineas_pedido= data_cleaning.to_snake_case(df_lineas_pedido)
        df_pedidos = data_cleaning.to_snake_case(df_pedidos)
        df_productos = data_cleaning.to_snake_case(df_productos)
        df_provincias = data_cleaning.to_snake_case(df_provincias)
        df_destinos = data_cleaning.to_snake_case(df_destinos)
        
        df_pedidos_clientes = df_pedidos.merge(df_clientes, on="cliente_id", how='left')
        df_pedidos_clientes = df_pedidos_clientes.drop(columns=['cliente_id', "nombre", "fecha_registro"])

        df_pedidos_clientes_destinos = df_pedidos_clientes.merge(df_destinos, on="destino_id", how='left')
        df_lineas_pedido_pedidos = df_lineas_pedido.merge(df_pedidos_clientes_destinos, on="pedido_id", how='left')


        df_lineas_pedido_pedidos_productos = df_lineas_pedido_pedidos.merge(df_productos, on="producto_id", how='left')

        df_lineas_pedido_pedidos_productos = df_lineas_pedido_pedidos_productos.drop(columns=['linea_pedido_id', "producto_id", "destino_id"])
        
        df_lineas_pedido_pedidos_productos = df_lineas_pedido_pedidos_productos.rename(columns={"nombre_completo":"destino", "nombre":"producto", "cantidad":"cantidad_producto", "email": "email_cliente"}, errors="raise")
        df_lineas_pedido_pedidos_productos = df_lineas_pedido_pedidos_productos.reindex(['pedido_id', 'fecha_pedido', 'producto', "cantidad_producto", "precio_venta", "tiempo_fabricacion_medio", "caducidad", "destino", "distancia_km", "coordenadas_gps", "email_cliente"], axis=1)

        #Export datasets clean
        #data_loaders.save_dataframe_to_csv(df_clientes,  paths.DATA_PROCESSED / "dboClientes.csv")
        #data_loaders.save_dataframe_to_csv(df_lineas_pedido, paths.DATA_PROCESSED / "dboLineasPedido.csv")
        #data_loaders.save_dataframe_to_csv(df_pedidos, paths.DATA_PROCESSED / "dboPedidos.csv")
        #data_loaders.save_dataframe_to_csv(df_productos, paths.DATA_PROCESSED / "dboProductos.csv")
        #data_loaders.save_dataframe_to_csv(df_provincias, paths.DATA_PROCESSED / "dboProvincias.csv")
        #data_loaders.save_dataframe_to_csv(df_destinos, paths.DATA_PROCESSED / "dboDestinos.csv")
        #data_loaders.save_dataframe_to_csv(df_destinos_provincia, paths.DATA_PROCESSED / "dboDestinos.csv")
        #data_loaders.save_dataframe_to_csv(df_pedidos_clientes,  paths.DATA_PROCESSED / "dboPedidos.csv")
        data_loaders.save_dataframe_to_csv(df_lineas_pedido_pedidos_productos,  paths.DATA_PROCESSED / "pedidos.csv")
        # Merge/Unify data

        return df_lineas_pedido_pedidos_productos;

        #Export unify data



        
if __name__ == "__main__":
    run()