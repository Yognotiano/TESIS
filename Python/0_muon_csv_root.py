# Importa las clases necesarias desde ROOT para trabajar con archivos .root y ntuples
from ROOT import TNtuple, TFile, TObject
import os

# Ruta base en tu MacBook (no se usa directamente en este script, pero puede ser útil para expandir)
base_dir = "/Users/yognotiano/Documents/todo/Lab/Datospy/"

# Crea un archivo ROOT nuevo llamado "data.root" para guardar los datos procesados
fout = TFile("data.root", "recreate")

# Crea un TNtuple para guardar datos con las variables: tiempo1, tiempo2, evento y posiciones (B1-B3, A1-A3)
tuple_data = TNtuple("matedata", "mate data", "tp1:tp2:evn:B1:B2:B3:A1:A2:A3")

# Función para verificar la consistencia de eventos (EVN) entre los tres archivos correspondientes a un conjunto de datos
def check_evn(data1, data2, data3, fname):
    """
    Verifica consistencia de los eventos (EVN) entre líneas consecutivas y entre archivos.
    """

    # Inicializa listas para almacenar errores detectados por cada archivo
    error1, error2, error3 = [], [], []

    # Función interna para verificar que los EVN sean consecutivos (sin saltos)
    def check_data(data, fname, suffix):
        errors = []
        for i in range(len(data) - 1):
            if (int(data[i][5]) + 1) != int(data[i + 1][5]):
                print(f"Error en el archivo {fname}_{suffix} en la línea {i + 1}")
                errors.extend([data[i][5], data[i + 1][5]])
        return errors

    # Verifica cada uno de los tres archivos
    error1 = check_data(data1, fname, "1")
    error2 = check_data(data2, fname, "2")
    error3 = check_data(data3, fname, "3")

    # Compara los primeros y últimos EVN entre los tres archivos
    if not (int(data1[0][5]) == int(data2[0][5]) == int(data3[0][5])):
        print(f"Diferencia en el EVN inicial entre archivos: {fname}")
    if not (int(data1[-1][5]) == int(data2[-1][5]) == int(data3[-1][5])):
        print(f"Diferencia en el EVN final entre archivos: {fname}")

    return error1, error2, error3

# Función para obtener coordenadas B y A de un archivo y descartar eventos con errores
def get_coordinates_single(data, error1, error2, error3):
    """
    Procesa datos de un solo archivo y calcula posiciones (A y B) a partir de los bits de datos.
    """

    # Inicializa listas de posiciones y variables asociadas
    pos_B, pos_A, pos_evn, pos_tp1, pos_tp2 = [], [], [], [], []

    for i in range(len(data)):
        try:
            evn = int(data[i][5])
            # Ignora eventos dentro del rango con errores
            if evn in range(int(error1[0]), int(error1[1]) + 1) or \
               evn in range(int(error2[0]), int(error2[1]) + 1) or \
               evn in range(int(error3[0]), int(error3[1]) + 1):
                continue
        except IndexError:
            pass  # Si no hay errores para ese archivo

        try:
            # Concatena los valores hexadecimales de los bytes de posición
            pos_hex = data[i][1] + data[i][2] + data[i][3]
            pos_int = int(pos_hex, 16)               # Convierte el hex a entero
            pos_bin = format(pos_int, '0>24b')       # Convierte a binario de 24 bits
            pos_bit = [int(bit) for bit in pos_bin]  # Convierte a lista de bits

            # Determina la posición activa en los primeros 12 bits (B) y en los últimos 12 bits (A)
            pos_Bt = [j for j in range(12) if pos_bit[j] != 0]
                        #Es importante la resta porque despues en el arreglo saldrán números fuera del rango
            pos_At = [j - 12 for j in range(12, 24) if pos_bit[j] != 0]

            # Solo si hay una posición activa por parte (B y A), se almacena; si no, se asigna -1
            if len(pos_Bt) == len(pos_At) == 1:
                pos_B.append(pos_Bt)
                pos_A.append(pos_At)
            else:
                pos_B.append([-1])
                pos_A.append([-1])

            # Guarda EVN y tiempos tp1, tp2
            pos_evn.append(data[i][5])
            pos_tp1.append(data[i][0])
            pos_tp2.append(data[i][4])
        except (ValueError, IndexError):
            print(f"Error procesando la línea: {data[i]}")

    return pos_B, pos_A, pos_evn, pos_tp1, pos_tp2

# Recorre las subcarpetas y archivos de datos en el directorio actual
for root, _, files in os.walk('./'):
    # Filtra archivos que corresponden al primer sensor ("m101") en la estructura esperada
    mate_files = [f for f in files if f.endswith("_06h00_mate-m101.txt")]

    for mate_file in mate_files:
        # Construye el prefijo de archivo para acceder también a m102 y m103
        file_prefix = os.path.join(root, mate_file.replace("_06h00_mate-m101.txt", ""))
        print(f"Leyendo archivo para {file_prefix}")

        try:
            # Lee los tres archivos correspondientes a un conjunto de datos
            data1 = [l.split(",") for l in open(file_prefix + "_06h00_mate-m101.txt").readlines()]
            data2 = [l.split(",") for l in open(file_prefix + "_06h00_mate-m102.txt").readlines()]
            data3 = [l.split(",") for l in open(file_prefix + "_06h00_mate-m103.txt").readlines()]
        except FileNotFoundError:
            print(f"Archivo no encontrado: {file_prefix}")
            continue

        # Verifica consistencia de eventos entre los tres archivos
        error1, error2, error3 = check_evn(data1, data2, data3, file_prefix)

        # Procesa cada archivo individualmente para obtener coordenadas y tiempos
        pos1_B, pos1_A, pos1_evn, pos1_tp1, pos1_tp2 = get_coordinates_single(data1, error1, error2, error3)
        pos2_B, pos2_A, pos2_evn, pos2_tp1, pos2_tp2 = get_coordinates_single(data2, error1, error2, error3)
        pos3_B, pos3_A, pos3_evn, pos3_tp1, pos3_tp2 = get_coordinates_single(data3, error1, error2, error3)

        # Llenado del TNtuple con los datos procesados
        for j in range(len(pos1_B)):
            try:
                tuple_data.Fill(
                    int(pos1_tp1[j]), int(pos1_tp2[j]), int(pos1_evn[j]),
                    int(pos1_B[j][0]), int(pos2_B[j][0]), int(pos3_B[j][0]),
                    int(pos1_A[j][0]), int(pos2_A[j][0]), int(pos3_A[j][0])
                )
            except IndexError:
                print(f"Error llenando TNtuple para índice {j}")

# Una vez procesado todo, se escribe el archivo ROOT en disco
print("Escribiendo archivo final...")
fout.Write("", TObject.kOverwrite)
fout.Close()
print("Archivo ROOT generado correctamente: data.root")
