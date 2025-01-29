from beammech import solve, Load
import numpy as np
import matplotlib.pyplot as plt

# Beam properties
length = 605  # 1 meter in mm
supports = (0, 605)  # Simply supported at both ends

# Load at the center (500 mm)
loads = [Load(kg=3, pos=250)]  # 1 kg load at the center

# Material and cross-section properties
E = 190000  # Young's modulus in N/mm² (steel)
b = 310  # Width in mm
h = 20  # Height in mm
I = (b * h**3) / 12  # Moment of inertia
EI = E * I  # Bending stiffness
GA = 1e6  # Shear rigidity (approximate, large value to ignore shear effects)
top = h / 2  # Distance from neutral axis to top surface
bottom = -h / 2  # Distance from neutral axis to bottom surface

# Solve the beam problem
results = solve(length, supports, loads, EI, GA, top, bottom, shear=False)

# Create a figure with two subplots side by side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))

# Plot real deflection along the beam length
ax1.plot(np.arange(length + 1), results.y, label='Deflection (mm)', color='blue', linewidth=2)
ax1.set_xlabel('Position along the beam (mm)', fontsize=12)
ax1.set_ylabel('Deflection (mm)', fontsize=12)
ax1.set_title('Beam Deflection Under Central Load', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend(fontsize=12)
ax1.set_xlim(-300, 1000)
max_deflection = max(results.y)
ax1.set_ylim(-1.5 * max_deflection, 1.5 * max_deflection)
ax1.yaxis.set_major_formatter(plt.FormatStrFormatter('%.6f'))

# Plot bending moment along the beam length
ax2.plot(np.arange(length + 1), results.M, label='Bending Moment', color='red', linewidth=2)
ax2.set_xlabel('Position along the beam (mm)', fontsize=12)
ax2.set_ylabel('Bending Moment (Nmm)', fontsize=12)
ax2.set_title('Bending Moment Under Central Load', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend(fontsize=12)
max_bendingMoment = max(results.M)
ax2.set_ylim(-0.5 * max_bendingMoment, 1.5 * max_bendingMoment)
ax2.set_xlim(-300, 1000)

# Show the plots
plt.tight_layout()
plt.show()

# Print key results
print(f"Maximum deflection: {max(results.y):.6f} mm")
print(f"Maximum bending moment: {max(results.M):.2f} Nmm")
print(f"Reaction forces: R1 = {results.R[0].size:.2f} N, R2 = {results.R[1].size:.2f} N")