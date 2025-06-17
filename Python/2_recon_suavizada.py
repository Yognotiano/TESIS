#!/usr/bin/env python3
"""
plot_muon_reconstruction_smoothed_ticks_grid.py

Reconstrucción 3D de trayectorias suavizadas y filtradas, con placas:
- Placa 3 (superior) en z = 124.7 cm, coordenadas (A3,B3)
- Placa 2 (media)    en z = 62.2  cm, coordenadas (A2,B2)
- Placa 1 (inferior) en z = 0.0   cm, coordenadas (A1,B1)

Se añade graduación de 3 cm en los ejes X e Y, y las placas muestran
líneas de cuadrícula cada 3 cm, trazadas perpendicularmente.
"""

import uproot
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# Parámetros de geometría
width_cm = 36.0            # ancho total de cada placa (cm)
Nch = 12                   # número de canales por eje
ch_width = width_cm / Nch  # ancho de canal (cm)
z_sup, z_med, z_inf = 124.7, 62.2, 0.0  # posiciones de placas en cm

# Límites de filtrado
R_tol = 1.0                 # residuo máximo permitido (cm)
theta_tol = np.deg2rad(5)   # ángulo máximo permitido (rad)

# Cuántos eventos muestrear
N_show = 100

# Abrir ROOT y extraer datos
f = uproot.open("data.root")
tree = f["matedata"]
arr = tree.arrays(["A1","B1","A2","B2","A3","B3"], library="np")

# Convertir canales a coordenadas centradas
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

# Muestreo de índices
np.random.seed(0)
indices = np.random.choice(len(X['sup']), size=min(N_show, len(X['sup'])), replace=False)

# Preparar figura
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(111, projection="3d")

# Crear malla para placas con paso de 3 cm
grid = np.arange(-width_cm/2, width_cm/2 + 1e-6, 3)
xx, yy = np.meshgrid(grid, grid)

# Dibujar placas con superficie + dos juegos de líneas perpendiculares
for z0 in (z_sup, z_med, z_inf):
    zz = np.full_like(xx, z0)
    # 1) Superficie semitransparente SIN líneas
    ax.plot_surface(
        xx, yy, zz,
        color='lightgray',
        alpha=0.3,
        linewidth=0,
        rstride=1, cstride=1,
        antialiased=True
    )
    # 2) Líneas paralelas al eje X
    ax.plot_wireframe(
        xx, yy, zz,
        rcount=xx.shape[0],   # tantas “filas” como puntos en Y
        ccount=1,             # sólo 1 “columna” → líneas paralelas a X
        color="#6ED3C2FF",
        linewidth=0.3,
        alpha=0.6
    )
    # 3) Líneas paralelas al eje Y
    ax.plot_wireframe(
        xx, yy, zz,
        rcount=1,             # sólo 1 “fila” → líneas paralelas a Y
        ccount=yy.shape[1],   # tantas “columnas” como puntos en X
        color="#6ED3C2FF",
        linewidth=0.3,
        alpha=0.6
    )

# Suavizar y filtrar tracks
for i in indices:
    xs = np.array([X['sup'][i], X['med'][i], X['inf'][i]])
    ys = np.array([Y['sup'][i], Y['med'][i], Y['inf'][i]])
    # Ajuste lineal
    px = np.polyfit(Z_vals, xs, 1)  # [slope, intercept]
    py = np.polyfit(Z_vals, ys, 1)
    # Valores ajustados
    xs_fit = px[0]*Z_vals + px[1]
    ys_fit = py[0]*Z_vals + py[1]
    # Residuos
    resid = np.sqrt((xs - xs_fit)**2 + (ys - ys_fit)**2)
    if resid.max() > R_tol:
        continue
    # Ángulo entre segmentos originales
    v = np.array([xs[1]-xs[0], ys[1]-ys[0], Z_vals[1]-Z_vals[0]])
    w = np.array([xs[2]-xs[1], ys[2]-ys[1], Z_vals[2]-Z_vals[1]])
    cosang = np.dot(v, w) / (np.linalg.norm(v)*np.linalg.norm(w))
    theta = np.arccos(np.clip(cosang, -1, 1))
    if theta > theta_tol:
        continue
    # Dibujar curva suave
    z_line = np.linspace(z_sup, z_inf, 200)
    x_line = px[0]*z_line + px[1]
    y_line = py[0]*z_line + py[1]
    ax.plot(x_line, y_line, z_line, linewidth=1)

# Ajustes finales
ticks = grid
ax.set_xticks(ticks)
ax.set_yticks(ticks)

ax.set_xlabel("X (cm)")
ax.set_ylabel("Y (cm)")
ax.set_zlabel("Z (cm)")
ax.set_xlim(-width_cm/2, width_cm/2)
ax.set_ylim(-width_cm/2, width_cm/2)
ax.set_zlim(z_inf, z_sup)
ax.set_title("Trayectorias suavizadas y filtradas\nGraduación y retícula XY cada 3 cm")
ax.view_init(elev=25, azim=45)
plt.tight_layout()
plt.show()
