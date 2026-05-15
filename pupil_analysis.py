#%%
import numpy as np
import matplotlib.pyplot as plt

def generate_powerpoint_plots(rms_aberration=0.42, fill_factor=0.8):
    """
    Generates a 2-panel dashboard (2D and 1D) with large fonts for presentations.
    Includes modulator borders and effective modulation area markers.
    """
    # 1. High-resolution grid
    n_points = 400 
    x = np.linspace(-1.2, 1.2, n_points) # Wider x to show modulator edges
    y = np.linspace(-1.2, 1.2, n_points)
    X, Y = np.meshgrid(x, y)
    
    rho = np.sqrt(X**2 + Y**2)
    
    # Raw (Non-Normalized) Zernike Spherical Aberration (6*rho^4 - 6*rho^2 + 1)
    z_spherical = (6*rho**4 - 6*rho**2 + 1)
    phase = rms_aberration * z_spherical
    
    # Apply mask for the MODULATOR first (rho <= 1.0)
    mod_mask = rho <= 1.0
    phase_mod = phase.copy()
    phase_mod[~mod_mask] = np.nan
    
    # Apply mask for the OBJECTIVE (Effective Modulation Area, e.g. 80%)
    obj_mask = rho <= fill_factor
    phase_obj = phase.copy()
    phase_obj[~obj_mask] = np.nan

    # 2. Setup Figure for PowerPoint
    plt.rcParams.update({'font.size': 20}) 
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 11)) # Wider and taller
    fig.patch.set_facecolor('white')

    # --- Panel 1: 2D Interpolated Map ---
    im = ax1.imshow(phase_mod, cmap='RdBu_r', extent=[-1.2, 1.2, -1.2, 1.2], 
                    origin='lower', interpolation='bicubic', vmin=-0.5, vmax=0.5)
    cbar = plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.08) # More padding for colorbar
    cbar.ax.set_title('rad', fontsize=24, pad=25)
    
    # Outline the Effective Area
    circle = plt.Circle((0, 0), fill_factor, color='green', fill=False, lw=4, ls='--')
    ax1.add_artist(circle)
    # Move label further down to avoid overlap
    ax1.text(0, -1.45, "Effective Modulation Area", color='green', 
             ha='center', fontsize=20, fontweight='bold')
    ax1.set_axis_off()

    # --- Panel 2: 1D Radial Profile ---
    slice_idx = n_points // 2
    ax2.plot(x, phase[slice_idx, :], color='grey', lw=3, alpha=0.2, label='Full Pattern')
    ax2.plot(x[obj_mask[slice_idx, :]], phase[slice_idx, obj_mask[slice_idx, :]], 
             color='firebrick', lw=8, label='Effective Modulation')
    
    # Borders and Shading
    ax2.axvspan(-fill_factor, fill_factor, color='green', alpha=0.05, label='Effective Modulation Area')
    ax2.axvline(-fill_factor, color='green', ls='-', lw=4, alpha=0.5)
    ax2.axvline(fill_factor, color='green', ls='-', lw=4, alpha=0.5)
    
    # Modulator Edges - Moved text higher to avoid axis
    ax2.axvline(-1.0, color='black', ls='--', lw=3, alpha=0.4)
    ax2.axvline(1.0, color='black', ls='--', lw=3, alpha=0.4)
    ax2.text(-1.0, 0.6, "Modulator\nEdge", color='grey', ha='center', fontsize=18, fontweight='bold')
    ax2.text(1.0, 0.6, "Modulator\nEdge", color='grey', ha='center', fontsize=18, fontweight='bold')
    
    ax2.set_xlabel('Normalized Coordinate', fontsize=28, labelpad=25)
    ax2.set_ylabel('Phase (rad)', fontsize=28, labelpad=25)
    ax2.set_ylim(-0.5, 0.5)
    ax2.set_xlim(-1.4, 1.4) # Slightly wider X to fit labels
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=24, pad=10)

    # --- Add Optical Parameters Box ---
    param_text = (
        r"$\lambda$ = 532 nm | NA = 0.5 | 1 mm Glass" "\n"
        r"Aberration: $Z_{11}$ (Spherical)"
    )
    fig.text(0.5, 0.05, param_text, ha='center', fontsize=24, 
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='grey', boxstyle='round,pad=0.8'))

    # Final Adjustments
    plt.tight_layout(pad=6.0, rect=[0, 0.1, 1, 0.95]) 
    fig.subplots_adjust(wspace=0.5, bottom=0.2) 
    plt.show()

if __name__ == "__main__":
    generate_powerpoint_plots(rms_aberration=0.42, fill_factor=0.8)

if __name__ == "__main__":
    generate_powerpoint_plots(rms_aberration=0.42, fill_factor=0.8)
