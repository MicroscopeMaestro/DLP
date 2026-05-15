#%%
import numpy as np
import matplotlib.pyplot as plt

def generate_astigmatism_plots(zernike_coeff=0.42):
    """
    Generates a 2-panel dashboard (2D and 1D) for Astigmatism.
    Optimized for PowerPoint presentations.
    """
    # 1. High-resolution grid
    n_points = 400 
    x = np.linspace(-1, 1, n_points)
    y = np.linspace(-1, 1, n_points)
    X, Y = np.meshgrid(x, y)
    
    rho = np.sqrt(X**2 + Y**2)
    mask = rho <= 1.0
    
    # Vertical Astigmatism (Z5 in Noll): x^2 - y^2
    # Non-normalized version as per previous request
    z_astig = (X**2 - Y**2)
    phase = zernike_coeff * z_astig
    
    # Apply mask
    phase_masked = phase.copy()
    phase_masked[~mask] = np.nan

    # 2. Setup Figure for PowerPoint (Wide Format)
    plt.rcParams.update({'font.size': 16}) 
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.patch.set_facecolor('white')

    # --- Panel 1: 2D Interpolated Map ---
    im = ax1.imshow(phase_masked, cmap='RdBu_r', extent=[-1, 1, -1, 1], 
                    origin='lower', interpolation='bicubic', vmin=-0.5, vmax=0.5)
    ax1.set_title("2D Phase Map (Astigmatism)", fontsize=26, fontweight='bold', pad=30)
    cbar = plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
    cbar.ax.set_title('rad', fontsize=20, pad=15)
    ax1.set_axis_off()

    # --- Panel 2: 1D Profile (Diagonal Slice) ---
    # For astigmatism (x^2 - y^2), the most interesting slice is along x (max/min)
    slice_idx = n_points // 2
    ax2.plot(x, phase[slice_idx, :], color='firebrick', lw=5, label='X-axis Profile')
    # Add Y-axis profile to show the opposite curvature
    ax2.plot(y, phase[:, slice_idx], color='steelblue', lw=5, ls='--', label='Y-axis Profile')
    
    ax2.set_title(f"1D Slices ($Z_{{5}}$ = {zernike_coeff})", fontsize=26, fontweight='bold', pad=30)
    ax2.set_xlabel('Normalized Pupil Coordinate', fontsize=22, labelpad=15)
    ax2.set_ylabel('Phase (rad)', fontsize=22, labelpad=15)
    ax2.set_ylim(-0.5, 0.5)
    ax2.set_xlim(-1.1, 1.1)
    ax2.axhline(0, color='black', lw=2, ls='-')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=18)
    
    # Increase tick sizes
    ax2.tick_params(axis='both', which='major', labelsize=18)

    # --- Add Optical Parameters Box ---
    param_text = (
        r"$\lambda$ = 532 nm | NA = 0.5 (Olympus 20X)" "\n"
        r"Medium: Air $\rightarrow$ 1 mm Glass" "\n"
        r"Aberration: $Z_{5}$ (Astigmatism)"
    )
    fig.text(0.5, 0.05, param_text, ha='center', fontsize=18, 
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='grey', boxstyle='round,pad=0.5'))

    plt.tight_layout(pad=4.0, rect=[0, 0.1, 1, 1]) 
    fig.subplots_adjust(wspace=0.4) 
    plt.show()

if __name__ == "__main__":
    generate_astigmatism_plots(zernike_coeff=0.42)
