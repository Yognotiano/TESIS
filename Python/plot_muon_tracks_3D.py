#!/usr/bin/env python3
"""
plot_muon_tracks_3d_clipped.py

Lee el CSV (tracks.csv) con slope_x y slope_y, y grafica varias trayectorias
en 3D colocando las coordenadas X e Y en el plano horizontal (ancho 36 cm)
y Z en vertical, truncando cada rayo para que no salga de |X|,|Y|<=18 cm.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# Parámetros
CSV_FILE    = "tracks.csv"
z_max       = 62.5                     # [cm] distancia al plano medio
half_width  = 18.0                     # [cm] medio ancho en X e Y
N_tracks    = 50                       # cuántas pistas muestrear
N_pts       = 100                      # puntos por línea

# Carga de datos
df = pd.read_csv(CSV_FILE)
slopes_x = df["slope_x"].values
slopes_y = df["slope_y"].values

# Muestreo aleatorio de índices
np.random.seed(0)
idx = np.random.choice(len(df), size=min(N_tracks, len(df)), replace=False)

# Preparar figura 3D
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

for i in idx:
    sx = slopes_x[i]
    sy = slopes_y[i]
    # Cálculo de z límite por X e Y
    lim_x = half_width/abs(sx) if sx!=0 else z_max
    lim_y = half_width/abs(sy) if sy!=0 else z_max
    lim   = min(z_max, lim_x, lim_y)
    # Generar segmento de z dentro de [-lim, +lim]
    z_line = np.linspace(-lim, +lim, N_pts)
    x_line = sx * z_line
    y_line = sy * z_line
    ax.plot(x_line, y_line, z_line, linewidth=1)

# Ajustar límites de los ejes
ax.set_xlim(-half_width, half_width)
ax.set_ylim(-half_width, half_width)
ax.set_zlim(-z_max, z_max)

# Etiquetas y título
ax.set_xlabel("X (cm)")
ax.set_ylabel("Y (cm)")
ax.set_zlabel("Z (cm)")
ax.set_title("Trayectorias 3D de muones (clip a XY=±18 cm)")

# Vista opcional
ax.view_init(elev=30, azim=45)

plt.tight_layout()
plt.show()

