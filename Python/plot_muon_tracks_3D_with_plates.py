#!/usr/bin/env python3
"""
plot_muon_tracks_3d_with_plates.py

Lee el CSV (tracks.csv) con slope_x y slope_y, y grafica varias trayectorias
en 3D (clip a |X|,|Y|<=18 cm) junto con las placas de 36×36 cm² en z=-62.5,0,+62.5 cm.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# Parámetros
CSV_FILE    = "tracks.csv"
z_planes    = np.array([-62.5, 0.0, 62.5])  # [cm]
half_width  = 18.0                          # [cm]
N_tracks    = 50
N_pts       = 100

# Carga de datos
df = pd.read_csv(CSV_FILE)
sx_arr = df["slope_x"].values
sy_arr = df["slope_y"].values

# Muestreo de pistas
np.random.seed(0)
idx = np.random.choice(len(df), size=min(N_tracks, len(df)), replace=False)

# Preparamos la figura 3D
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

# Dibujar placas como superficies semitransparentes
# Creamos una malla 2×2 para las esquinas de cada placa
xx, yy = np.meshgrid(
    np.linspace(-half_width, half_width, 2),
    np.linspace(-half_width, half_width, 2)
)
for z0 in z_planes:
    zz = np.full_like(xx, z0)
    ax.plot_surface(
        xx, yy, zz,
        color='gray', alpha=0.3, edgecolor='k', linewidth=0.5
    )

# Dibujar las trayectorias recortadas
for i in idx:
    sx = sx_arr[i]
    sy = sy_arr[i]
    # límite en z para no sobrepasar X,Y
    lim_x = half_width/abs(sx) if sx!=0 else z_planes.max()
    lim_y = half_width/abs(sy) if sy!=0 else z_planes.max()
    lim   = min(z_planes.max(), lim_x, lim_y)
    # generamos el tramo
    z_line = np.linspace(-lim, +lim, N_pts)
    x_line = sx * z_line
    y_line = sy * z_line
    ax.plot(x_line, y_line, z_line, linewidth=1)

# Límites de ejes
ax.set_xlim(-half_width, half_width)
ax.set_ylim(-half_width, half_width)
ax.set_zlim(z_planes.min(), z_planes.max())

# Etiquetas
ax.set_xlabel("X (cm)")
ax.set_ylabel("Y (cm)")
ax.set_zlabel("Z (cm)")
ax.set_title("Trayectorias 3D de muones con placas de 36×36 cm²")

# Vista
ax.view_init(elev=30, azim=45)
plt.tight_layout()
plt.show()
