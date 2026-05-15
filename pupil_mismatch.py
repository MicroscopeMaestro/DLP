#%%
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift

def simulate_mismatch_interaction(scale_factor=0.6, lateral_shift=0.1, astig_val=2.0):
    """
    Shows how radial size mismatch amplifies PSF shifts from lateral misalignment.
    scale_factor: Ratio of Modulator size to Objective size (e.g., 0.6 = Underfilling).
    lateral_shift: Centering error (e.g., 0.1 = 10% of pupil radius).
    """
    n_points = 512
    x = np.linspace(-2, 2, n_points)
    y = np.linspace(-2, 2, n_points)
    X, Y = np.meshgrid(x, y)
    rho = np.sqrt(X**2 + Y**2)

    # 1. Objective Pupil (Reference)
    obj_pupil = (rho <= 1.0).astype(float)
    
    # 2. Modulator Phase Pattern
    # The pattern is 'shrunk' by scale_factor and 'shifted' by lateral_shift
    X_mod = (X - lateral_shift) / scale_factor
    Y_mod = Y / scale_factor
    
    # Apply Astigmatism on the modulator's coordinate system
    # Smaller scale_factor makes the gradients steeper!
    phase_mod = astig_val * (X_mod**2 - Y_mod**2)
    
    # 3. Combine
    complex_pupil = obj_pupil * np.exp(1j * phase_mod)
    
    # 4. PSF Calculation
    psf = np.abs(fftshift(fft2(fftshift(complex_pupil))))**2
    psf /= np.max(psf)

    # 5. Plotting
    plt.rcParams.update({'font.size': 14})
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor('white')

    # --- Panel 1: Pupil Geometry ---
    ax1 = fig.add_subplot(221)
    ax1.contour(X, Y, obj_pupil, levels=[0.5], colors='green', linewidths=3)
    # Show the modulator pattern center and effective size
    mod_circle = np.sqrt(X_mod**2 + Y_mod**2) <= 1.0
    ax1.contour(X, Y, mod_circle, levels=[0.5], colors='firebrick', linestyles='--')
    ax1.plot(lateral_shift, 0, 'rx', markersize=12, label='Mod Center')
    ax1.set_title(f"Alignment Error: Shift={lateral_shift}, Scale={scale_factor}", fontsize=18, fontweight='bold')
    ax1.set_xlabel("Pupil X")
    ax1.set_ylabel("Pupil Y")
    ax1.legend(["Obj Pupil", "Mod Center"], loc='upper right')
    ax1.set_aspect('equal')
    ax1.grid(alpha=0.2)

    # --- Panel 2: Resulting Phase Gradient ---
    ax2 = fig.add_subplot(222)
    phase_viz = phase_mod.copy()
    phase_viz[obj_pupil == 0] = np.nan
    im2 = ax2.imshow(phase_viz, cmap='RdBu_r', extent=[-2, 2, -2, 2])
    plt.colorbar(im2, ax=ax2, label="Phase (rad)")
    ax2.set_title("Phase seen by Objective Lens\n(Steeper gradients due to scale mismatch)", fontsize=18, fontweight='bold')
    ax2.set_axis_off()

    # --- Panel 3: Strong PSF Shift ---
    ax3 = fig.add_subplot(223)
    zoom = 120 # Wider zoom to see the strong shift
    center = n_points // 2
    psf_zoom = psf[center-zoom:center+zoom, center-zoom:center+zoom]
    ax3.imshow(psf_zoom, cmap='magma', extent=[-zoom, zoom, -zoom, zoom])
    ax3.axvline(0, color='white', ls=':', alpha=0.5)
    ax3.axhline(0, color='white', ls=':', alpha=0.5)
    ax3.set_title("Resulting Focal Spot Position\n(Strong Spatial 'Walk-off')", fontsize=18, fontweight='bold')
    ax3.set_xlabel("Sample Plane")

    # --- Panel 4: Mathematical Analysis ---
    ax4 = fig.add_subplot(224)
    ax4.axis('off')
    analysis_text = (
        "Why the shift is amplified:\n\n"
        f"1. Scale Error ($S$): {scale_factor}\n"
        fr"2. Alignment Error ($\Delta$): {lateral_shift}" "\n\n"
        r"$\Phi \propto \frac{Astig \cdot (x-\Delta)^2}{S^2}$" "\n\n"
        r"Local Tilt $\propto \frac{\partial\Phi}{\partial x} \approx \frac{2 \cdot Astig \cdot \Delta}{S^2}$" "\n\n"
        "Because the scale factor is squared in the denominator,\n"
        "underfilling the objective (S < 1) multiplies the\n"
        "spatial shift by a factor of $1/S^2$."
    )
    ax4.text(0.1, 0.8, analysis_text, fontsize=16, verticalalignment='top', linespacing=1.6)

    plt.tight_layout(pad=4.0)
    plt.show()

if __name__ == "__main__":
    # Simulate a significant interaction: 60% scale and 10% shift
    simulate_mismatch_interaction(scale_factor=0.6, lateral_shift=0.1, astig_val=2.0)
