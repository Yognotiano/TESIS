#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para calcular el ángulo de incidencia asociado a una coordenada (A2, B2)
elegida en la placa m102 y además generar una imagen 3D que dibuje todas las trayectorias
desde cada punto (A1, B1) relacionado hacia (A2, B2).

- Lee el TNtuple "matedata" del archivo ROOT.
- Pide por terminal al usuario la coordenada (A2, B2) a analizar.
- Filtra todas las entradas con esa (A2, B2) y extrae sus correspondientes (A1, B1).
- Convierte los índices A, B en posiciones físicas usando:
      a = 0.36 m   (ancho total dividido en 12 strips → pitch = a/12)
      h = 0.61 m   (distancia entre placa m101 y m102)
- Para cada evento individual:
      • Calcula Δx = (A2 - A1) · pitch,    Δy = (B2 - B1) · pitch,    Δz = h
      • Ángulo_i = arctan( √(Δx² + Δy²) / h )
- Dibuja en 3D todas las líneas que conectan cada (A1, B1, 0) con (A2, B2, h).
- Además, si hay al menos 2 puntos, realiza un ajuste lineal (mínimos cuadrados)
  en el plano de m101 y calcula el ángulo promedio.

Requiere:
    • ROOT con PyROOT instalado.
    • numpy (para el ajuste lineal).
    • math (funciones trigonométricas).
    • matplotlib (para generar la imagen 3D).

Autor: [Tu Nombre]
Fecha: [Fecha actual]
"""

import sys
import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Importar las clases de ROOT
from ROOT import TFile, TNtuple

def main():
    # 1) Definir parámetros físicos en metros
    a_m = 0.36    # [m], ancho total de la placa (12 strips)
    h_m = 0.61    # [m], separación vertical entre m101 y m102
    pitch = a_m / 12.0  # Cada índice entero A o B se convierte a metros

    # 2) Abrir data.root y obtener el TNtuple
    archivo = TFile.Open("data.root", "READ")
    if not archivo or archivo.IsZombie():
        print("Error: no se pudo abrir 'data.root'. Verifica que exista.")
        sys.exit(1)

    ntuple = archivo.Get("matedata")
    if not ntuple:
        print("Error: no se encontró el TNtuple 'matedata' en data.root.")
        sys.exit(1)

    # 3) Leer (A2, B2) desde la terminal
    try:
        A2_sel = int(input("Ingresa A2 (entero entre 0 y 11): ").strip())
        B2_sel = int(input("Ingresa B2 (entero entre 0 y 11): ").strip())
    except ValueError:
        print("Error: debes ingresar valores enteros para A2 y B2.")
        sys.exit(1)

    if not (0 <= A2_sel <= 11 and 0 <= B2_sel <= 11):
        print("Error: A2 y B2 deben estar en el rango [0, 11].")
        sys.exit(1)

    # 4) Recorrer todas las entradas y recopilar (A1, B1) válidos
    lista_A1 = []
    lista_B1 = []
    angulos_evento = []

    n_entries = ntuple.GetEntries()
    for i in range(n_entries):
        ntuple.GetEntry(i)
        A2 = int(ntuple.A2)
        B2 = int(ntuple.B2)
        A1 = int(ntuple.A1)
        B1 = int(ntuple.B1)

        # Descartar si (A2,B2) o (A1,B1) no están en [0,11]
        if not (0 <= A2 <= 11 and 0 <= B2 <= 11 and 0 <= A1 <= 11 and 0 <= B1 <= 11):
            continue

        # Si coincide con la coordenada seleccionada, lo guardamos
        if A2 == A2_sel and B2 == B2_sel:
            lista_A1.append(A1)
            lista_B1.append(B1)
            dx = (A2 - A1) * pitch
            dy = (B2 - B1) * pitch
            dz = h_m
            dist_horiz = math.sqrt(dx*dx + dy*dy)
            ang_i = math.degrees(math.atan2(dist_horiz, dz))
            angulos_evento.append((i, A1, B1, ang_i))

    archivo.Close()

    # Si no hay eventos, salir
    if len(lista_A1) == 0:
        print(f"No se encontró ningún evento con (A2, B2) = ({A2_sel}, {B2_sel}).")
        sys.exit(0)

    # 5) Mostrar en consola todos los puntos (A1,B1) relacionados
    print(f"\n--- Puntos (A1, B1) relacionados con (A2, B2) = ({A2_sel}, {B2_sel}) ---")
    for a1, b1 in zip(lista_A1, lista_B1):
        print(f"({a1}, {b1})")

    # Mostrar ángulos individuales por evento
    print("\n--- Ángulos individuales por evento ---")
    print("Índice_Evento \t A1 \t B1 \t Ángulo [grados]")
    for idx, A1_ev, B1_ev, ang_ev in angulos_evento:
        print(f"{idx:12d} \t {A1_ev:2d} \t {B1_ev:2d} \t {ang_ev:8.3f}")

    # 6) Ajuste lineal por mínimos cuadrados en m101 (antes de plot 3D)
    x1_arr = np.array(lista_A1, dtype=float) * pitch
    y1_arr = np.array(lista_B1, dtype=float) * pitch

    if len(x1_arr) >= 2:
        m, c = np.polyfit(x1_arr, y1_arr, 1)
        ang_fit = math.degrees(math.atan2(pitch * math.sqrt(1 + m*m), h_m))
        print("Lo anterior son las coor A1,B1 relacionadas y el angulo de incidencia ")
        print("\n--- Resultados del Ajuste Lineal (mínimos cuadrados) ---")
        print(f"Número de puntos usados en el ajuste: {len(x1_arr)}")
        print(f"Pendiente m = {m:.5f}")
        print(f"Intersección c = {c:.5f} m")
        print(f"Ángulo promedio (fit) = {ang_fit:.3f}°\n")
        print(f"Ecuación de la recta ajustada: y = ({m:.5f})·x + ({c:.5f})")
    else:
        print("\nNo hay suficientes puntos (mínimo 2) para realizar ajuste lineal.\n")

    # 7) Preparar datos físicos en metros para el gráfico 3D
    x2 = A2_sel * pitch
    y2 = B2_sel * pitch
    z2 = h_m

    x1_coords = [a1 * pitch for a1 in lista_A1]
    y1_coords = [b1 * pitch for b1 in lista_B1]
    z1_coords = [0.0] * len(lista_A1)  # Todos los A1,B1 están en z=0

    # 8) Dibujar en 3D con Matplotlib
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Dibujar cada trayectoria como línea desde (x1, y1, 0) a (x2, y2, h)
    for x1, y1, z1 in zip(x1_coords, y1_coords, z1_coords):
        ax.plot([x1, x2], [y1, y2], [z1, z2], color='blue', linewidth=1)

    # Marcar puntos de origen en z=0 y punto objetivo en z=h
    ax.scatter(x1_coords, y1_coords, z1_coords, c='red', s=30, label='(A1, B1) en z=0')
    ax.scatter([x2], [y2], [z2], c='green', s=60, label=f'(A2, B2) en z={h_m} m')

    # Etiquetas y límites
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    ax.set_title(f'Trayectorias 3D hacia (A2, B2) = ({A2_sel}, {B2_sel})')
    ax.set_xlim(0, a_m)
    ax.set_ylim(0, a_m)
    ax.set_zlim(0, h_m)
    ax.legend()

    plt.tight_layout()
    plt.show()

    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
