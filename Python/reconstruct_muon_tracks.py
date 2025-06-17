#!/usr/bin/env python3
"""
reconstruct_muon_tracks.py

Lee el TTree "muons" de muons_data.root, ajusta una línea a los hits
(Ai, Bi) en los tres planos definidos por z_positions, y calcula
la pendiente y el ángulo de incidencia en x–z e y–z para cada evento.

Salida: CSV con slope_x, slope_y, theta_x_deg, theta_y_deg.
"""

import uproot
import numpy as np
import pandas as pd
import argparse

def parse_args():
    p = argparse.ArgumentParser(
        description="Reconstruye trayectorias de muones desde muons_data.root"
    )
    p.add_argument(
        "-i","--input", default="muons_data.root",
        help="Archivo ROOT de entrada con TTree 'muons'"
    )
    p.add_argument(
        "-o","--output", default="tracks.csv",
        help="Nombre de archivo CSV de salida"
    )
    p.add_argument(
        "--z_positions", nargs=3, type=float,
        default=[0.0, 10.0, 20.0],
        help="Posiciones z de los planos (en las mismas unidades que uses)"
    )
    return p.parse_args()

def main():
    args = parse_args()

    # 1) Abre el ROOT y extrae las ramas
    tree = uproot.open(args.input)["muons"]
    arr = tree.arrays(["A1","B1","A2","B2","A3","B3"], library="np")

    # 2) Prepara posiciones z y constantes para el ajuste
    z = np.array(args.z_positions)
    z_mean = z.mean()
    denom = np.sum((z - z_mean)**2)

    # 3) Prealoca vectores de resultados
    n = len(arr["A1"])
    slopes_x = np.empty(n)
    slopes_y = np.empty(n)

    # 4) Loop sobre eventos
    for i in range(n):
        x = np.array([arr["B1"][i], arr["B2"][i], arr["B3"][i]])
        y = np.array([arr["A1"][i], arr["A2"][i], arr["A3"][i]])
        x_mean = x.mean()
        y_mean = y.mean()
        # pendiente = cov(z,x)/var(z)
        slopes_x[i] = np.sum((z - z_mean) * (x - x_mean)) / denom
        slopes_y[i] = np.sum((z - z_mean) * (y - y_mean)) / denom

    # 5) Ángulos en grados
    theta_x = np.degrees(np.arctan(slopes_x))
    theta_y = np.degrees(np.arctan(slopes_y))

    # 6) Guardar en CSV
    df = pd.DataFrame({
        "slope_x": slopes_x,
        "slope_y": slopes_y,
        "theta_x_deg": theta_x,
        "theta_y_deg": theta_y,
    })
    df.to_csv(args.output, index=False)
    print(f"Guardado {n} tracks en '{args.output}'")

if __name__ == "__main__":
    main()
