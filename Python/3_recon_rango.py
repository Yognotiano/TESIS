#!/usr/bin/env python3
"""
plot_muon_reconstruction_smoothed_ticks_grid.py

Reconstrucción 3D de trayectorias suavizadas y filtradas, con placas.
Permite seleccionar interactívamente el rango de filas (Row) a analizar.
"""

import uproot
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# Parámetros de geometría
width_cm = 36.0          # ancho total de cada placa (cm)
Nch = 12                 # número de canales por eje
ch_width = width_cm / Nch
z_sup, z_med, z_inf = 124.7, 62.2, 0.0

# Límites de filtrado
R_tol = 1.0                 # residuo máximo permitido (cm)
theta_tol = np.deg2rad(5)   # ángulo máximo permitido (rad)

# --- Entrada interactiva de filas a analizar ---
start_idx = int(input("Ingresa la Row de inicio (incial=0): "))
end_idx   = int(input("Ingresa la Row final  (final=3692189): "))

# Abre el fichero y extrae también el número de evento (evn)
f = uproot.open("data.root")
tree = f["matedata"]
arr = tree.arrays(["A1","B1","A2","B2","A3","B3","evn"], library="np")

# Muestra al usuario qué eventos corresponden a esas filas
evn_start = int(arr["evn"][start_idx])
evn_end   = int(arr["evn"][end_idx])
print(f"\nEstás analizando entre el evento {evn_start} (Row {start_idx}) "
      f"y el evento {evn_end} (Row {end_idx})\n")

# Conversión de canales a coordenadas centradas
offset = (Nch-1)/2 * ch_width
X = {
    'sup': arr["A3"]*ch_width - offset,
    'med': arr["A2"]*ch_width - offset,
    'inf': arr["A1"]*ch_width - offset
}
Y = {
    'sup': arr["B3"]*ch_width - offset,
    'med': arr["B2"]*ch_width - offset,
    'inf': arr["B1"]*ch_width - offset
}
Z_vals = np.array([z_sup, z_med, z_inf])

# Prepara lista de índices a iterar
indices = np.arange(start_idx, end_idx+1)

# Configura figura 3D
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(111, projection="3d")

# Dibuja placas con retícula cada 3 cm
grid = np.arange(-width_cm/2, width_cm/2 + 1e-6, 3)
xx, yy = np.meshgrid(grid, grid)
for z0 in (z_sup, z_med, z_inf):
    zz = np.full_like(xx, z0)
    ax.plot_surface(xx, yy, zz, color='lightgray', alpha=0.3, linewidth=0)
    ax.plot_wireframe(xx, yy, zz, rcount=xx.shape[0], ccount=1, linewidth=0.3, alpha=0.6)
    ax.plot_wireframe(xx, yy, zz, rcount=1, ccount=yy.shape[1], linewidth=0.3, alpha=0.6)

# Suaviza y filtra trayectorias dentro del rango
for i in indices:
    xs = np.array([X['sup'][i], X['med'][i], X['inf'][i]])
    ys = np.array([Y['sup'][i], Y['med'][i], Y['inf'][i]])
    # ajuste lineal
    px = np.polyfit(Z_vals, xs, 1)
    py = np.polyfit(Z_vals, ys, 1)
    xs_fit = px[0]*Z_vals + px[1]
    ys_fit = py[0]*Z_vals + py[1]
    # filtrado por residuo
    if np.sqrt(((xs - xs_fit)**2 + (ys - ys_fit)**2).max()) > R_tol:
        continue
    # filtrado por ángulo
    v = np.array([xs[1]-xs[0], ys[1]-ys[0], Z_vals[1]-Z_vals[0]])
    w = np.array([xs[2]-xs[1], ys[2]-ys[1], Z_vals[2]-Z_vals[1]])
    theta = np.arccos(np.clip(np.dot(v,w)/(np.linalg.norm(v)*np.linalg.norm(w)), -1,1))
    if theta > theta_tol:
        continue
    # traza curva suave
    z_line = np.linspace(z_sup, z_inf, 200)
    ax.plot(px[0]*z_line+px[1], py[0]*z_line+py[1], z_line, linewidth=1)

# Ajustes finales del gráfico
ticks = grid
ax.set_xticks(ticks); ax.set_yticks(ticks)
ax.set_xlabel("X (cm)"); ax.set_ylabel("Y (cm)"); ax.set_zlabel("Z (cm)")
ax.set_xlim(-width_cm/2, width_cm/2)
ax.set_ylim(-width_cm/2, width_cm/2)
ax.set_zlim(z_inf, z_sup)
ax.set_title("Trayectorias suavizadas y filtradas\nRetícula XY cada 3 cm")
ax.view_init(elev=25, azim=45)
plt.tight_layout()
plt.show()