#%%
import numpy as np
import matplotlib.pyplot as plt

def generate_sa_powerpoint_analysis(z11_coeff=0.42, fill_factor=0.8):
    """
    Generates a high-impact PowerPoint visualization of the SA-to-Defocus shift.
    """
    n_points = 600
    rho = np.linspace(-1.2, 1.2, n_points) 
    
    # Z11 = 6*rho^4 - 6*rho^2 + 1
    z11_full = z11_coeff * (6*rho**4 - 6*rho**2 + 1)
    
    # Objective Pupil Region (80%)
    obj_mask = np.abs(rho) <= fill_factor
    rho_crop = rho[obj_mask]
    z11_crop = z11_full[obj_mask]
    
    # Fit Defocus (a*rho^2 + c)
    coeffs = np.polyfit(rho_crop**2, z11_crop, 1)
    defocus_fit = coeffs[0] * rho**2 + coeffs[1]

    # PowerPoint Styling
    plt.rcParams.update({'font.size': 18}) # Large base font
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor('white')
    ax = fig.add_subplot(111)

    # 1. Plot Background (Unused Modulator Area)
    ax.plot(rho, z11_full, color='grey', lw=3, alpha=0.2, label='Pattern outside Pupil')
    
    # 2. Plot Phase seen by Objective (The "Active" part)
    ax.plot(rho_crop, z11_crop, color='firebrick', lw=8, label='Pupil Wavefront ($Z_{11}$)')
    
    # 3. Plot Effective Defocus
    ax.plot(rho_crop, defocus_fit[obj_mask], color='steelblue', lw=5, ls='--', 
            label='Effective Defocus (Axial Shift)')
    
    # 4. Highlight Pupil Areas
    # Objective Pupil
    ax.axvspan(-fill_factor, fill_factor, color='green', alpha=0.07)
    ax.axvline(-fill_factor, color='green', ls='-', lw=3, alpha=0.5)
    ax.axvline(fill_factor, color='green', ls='-', lw=3, alpha=0.5)
    ax.text(0, 1.15, "Effective Modulation Area", color='green', ha='center', fontsize=20, fontweight='bold')
    
    # Modulator Borders
    ax.axvline(-1.0, color='grey', ls='--', lw=2, alpha=0.8)
    ax.axvline(1.0, color='grey', ls='--', lw=2, alpha=0.8)
    ax.text(-1.0, -0.5, "Modulator\nEdge", color='grey', ha='center', fontsize=16, fontweight='bold')
    ax.text(1.0, -0.5, "Modulator\nEdge", color='grey', ha='center', fontsize=16, fontweight='bold')

    # Formatting for PowerPoint
    ax.set_title("Underfilled Spherical Aberration $\\rightarrow$ Axial Shift", fontsize=28, fontweight='bold', pad=40)
    ax.set_xlabel("Normalized Pupil Coordinate", fontsize=22, labelpad=15)
    ax.set_ylabel("Phase (rad)", fontsize=22, labelpad=15)
    ax.set_ylim(-0.6, 1.3)
    ax.set_xlim(-1.2, 1.2)
    ax.grid(True, axis='y', linestyle=':', alpha=0.5)
    
    # Legend at the bottom
    ax.legend(fontsize=16, loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=3, frameon=False)

    # Annotations
    ax.annotate("Quadratic Curvature\n(Parabolic)", xy=(0.4, 0.2), xytext=(0.8, -0.3),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", lw=2),
                fontsize=18, color='steelblue', fontweight='bold')

    # --- Add Optical Parameters Box ---
    param_text = (
        r"$\lambda$ = 532 nm | NA = 0.5 | 1 mm Glass" "\n"
        r"Aberration: $Z_{11}$ (Spherical)"
    )
    fig.text(0.5, 0.08, param_text, ha='center', fontsize=18, 
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='grey', boxstyle='round,pad=0.5'))

    plt.tight_layout(rect=[0, 0.15, 1, 1])
    plt.show()

if __name__ == "__main__":
    generate_sa_powerpoint_analysis(z11_coeff=0.42, fill_factor=0.8)
