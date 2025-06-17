#!/usr/bin/env python3
"""
plot_muon_reconstruction_corrected.py

Reconstrucción 3D de trayectorias evento a evento con placas:
- Placa 3 (superior) en z = 124.7 cm, coordenadas (A3,B3)
- Placa 2 (media)    en z = 62.2  cm, coordenadas (A2,B2)
- Placa 1 (inferior) en z = 0.0   cm, coordenadas (A1,B1)

Conecta (A3,B3)→(A2,B2)→(A1,B1) en 3D y dibuja las placas de 36×36 cm².
"""

import uproot
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --- Parámetros de geometría ---
width_cm = 36.0            # ancho total de cada placa (cm)
Nch = 12                   # número de canales por eje
ch_width = width_cm / Nch  # ancho de canal (cm)

# Posiciones z para cada placa
z_sup = 124.7  # placa superior (3)
z_med = 62.2   # placa media   (2)
z_inf = 0.0    # placa inferior(1)

# Cuántos eventos muestrear para graficar
N_show = 50

# --- Abrir ROOT y extraer ramas ---
f = uproot.open("data.root")
tree = f["matedata"]
arrays = tree.arrays(["A1","B1","A2","B2","A3","B3"], library="np")

# Offset para centrar canales en el medio de la placa
offset = (Nch - 1) / 2 * ch_width

# Mapear canales a coordenadas X,Y para cada placa
X_sup = arrays["A3"] * ch_width - offset
Y_sup = arrays["B3"] * ch_width - offset
X_med = arrays["A2"] * ch_width - offset
Y_med = arrays["B2"] * ch_width - offset
X_inf = arrays["A1"] * ch_width - offset
Y_inf = arrays["B1"] * ch_width - offset

# Muestrear índices aleatorios
np.random.seed(0)
idx = np.random.choice(len(X_sup), size=min(N_show, len(X_sup)), replace=False)

# --- Crear figura 3D ---
fig = plt.figure(figsize=(8,6))
ax = fig.add_subplot(111, projection="3d")

# Dibujar placas como superficies semitransparentes
xx, yy = np.meshgrid(
    np.linspace(-width_cm/2, width_cm/2, 2),
    np.linspace(-width_cm/2, width_cm/2, 2)
)
for z0 in (z_sup, z_med, z_inf):
    zz = np.full_like(xx, z0)
    ax.plot_surface(xx, yy, zz, color='gray', alpha=0.3, edgecolor='k')

# Dibujar trayectorias conectando superior→media→inferior
for i in idx:
    xs = [X_sup[i], X_med[i], X_inf[i]]
    ys = [Y_sup[i], Y_med[i], Y_inf[i]]
    zs = [z_sup, z_med, z_inf]
    ax.plot(xs, ys, zs, linewidth=0.8)

# Ajustes finales
ax.set_xlabel("X (cm)")
ax.set_ylabel("Y (cm)")
ax.set_zlabel("Z (cm)")
ax.set_xlim(-width_cm/2, width_cm/2)
ax.set_ylim(-width_cm/2, width_cm/2)
ax.set_zlim(z_inf, z_sup)
ax.set_title("Reconstrucción 3D de trayectorias de muones\n"
             "Placa superior (3) → media (2) → inferior (1)")
ax.view_init(elev=25, azim=45)
plt.tight_layout()
plt.show()
