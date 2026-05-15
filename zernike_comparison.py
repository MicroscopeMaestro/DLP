#%%
import numpy as np
import matplotlib.pyplot as plt

def plot_zernike_presentation(mode='spherical', coeff=0.42, fill_factor=0.8):
    """
    Generates presentation-ready plots for either Defocus or Spherical Aberration.
    mode: 'defocus' or 'spherical'
    """
    n_points = 400
    x = np.linspace(-1.2, 1.2, n_points)
    y = np.linspace(-1.2, 1.2, n_points)
    X, Y = np.meshgrid(x, y)
    rho = np.sqrt(X**2 + Y**2)
    
    # Define Polynomials (Non-normalized)
    if mode.lower() == 'defocus':
        z_poly = (2*rho**2 - 1)
        label = "$Z_4$"
        title_type = "Defocus"
    else: # Default to Spherical
        z_poly = (6*rho**4 - 6*rho**2 + 1)
        label = "$Z_{11}$"
        title_type = "Spherical Aberration"
        
    phase = coeff * z_poly
    
    # Masks
    mod_mask = rho <= 1.0
    obj_mask = rho <= fill_factor
    phase_mod = phase.copy()
    phase_mod[~mod_mask] = np.nan
    
    # 2. Setup Figure
    plt.rcParams.update({'font.size': 20}) 
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 11))
    fig.patch.set_facecolor('white')

    # --- Panel 1: 2D Phase Map ---
    im = ax1.imshow(phase_mod, cmap='RdBu_r', extent=[-1.2, 1.2, -1.2, 1.2], 
                    origin='lower', interpolation='bicubic', vmin=-0.5, vmax=0.5)
    cbar = plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.08)
    cbar.ax.set_title('rad', fontsize=24, pad=25)
    
    # Effective Area Marker
    circle = plt.Circle((0, 0), fill_factor, color='green', fill=False, lw=4, ls='--')
    ax1.add_artist(circle)
    ax1.text(0, -1.45, "Effective Modulation Area", color='green', ha='center', fontsize=20, fontweight='bold')
    ax1.set_axis_off()

    # --- Panel 2: 1D Radial Profile ---
    slice_idx = n_points // 2
    ax2.plot(x, phase[slice_idx, :], color='grey', lw=3, alpha=0.2)
    ax2.plot(x[obj_mask[slice_idx, :]], phase[slice_idx, obj_mask[slice_idx, :]], 
             color='firebrick', lw=8, label=f'Current {title_type}')
    
    # Boundaries
    ax2.axvspan(-fill_factor, fill_factor, color='green', alpha=0.05)
    ax2.axvline(-fill_factor, color='green', ls='-', lw=4, alpha=0.5)
    ax2.axvline(fill_factor, color='green', ls='-', lw=4, alpha=0.5)
    
    # Labels
    ax2.text(-1.0, 0.6, "Modulator\nEdge", color='grey', ha='center', fontsize=18, fontweight='bold')
    ax2.text(1.0, 0.6, "Modulator\nEdge", color='grey', ha='center', fontsize=18, fontweight='bold')
    
    ax2.set_xlabel('Normalized Coordinate', fontsize=28, labelpad=25)
    ax2.set_ylabel('Phase (rad)', fontsize=28, labelpad=25)
    ax2.set_ylim(-0.5, 0.7) # Slightly higher limit for Defocus peaks
    ax2.set_xlim(-1.4, 1.4)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=24, pad=10)

    # --- Parameters Box ---
    param_text = (
        r"$\lambda$ = 532 nm | NA = 0.5 | 1 mm Glass" "\n"
        f"Aberration: {label} ({title_type})"
    )
    fig.text(0.5, 0.05, param_text, ha='center', fontsize=24, 
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='grey', boxstyle='round,pad=0.8'))

    plt.tight_layout(pad=6.0, rect=[0, 0.1, 1, 0.95]) 
    fig.subplots_adjust(wspace=0.5, bottom=0.2) 
    plt.show()

if __name__ == "__main__":
    # Generate Defocus
    plot_zernike_presentation(mode='defocus', coeff=0.42)
    # Generate Spherical
    plot_zernike_presentation(mode='spherical', coeff=0.42)
