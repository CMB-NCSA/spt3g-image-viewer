from astropy.io import fits
from astropy.visualization import simple_norm
import matplotlib
matplotlib.use("Agg")  # No GUI backend
import matplotlib.pyplot as plt
from PIL import Image

from config import FILE_PREFIX

def fits_to_png(fits_path, png_path, stretch='linear', percent=95, cmap='gray'):
    # Load FITS
    hdu = fits.open(fits_path)[1]
    data = hdu.data

    # Handle 3D or invalid data
    if data.ndim > 2:
        data = data[0]
    if not isinstance(data, (list, tuple)):
        data = data.astype('float')

    # Normalize image
    norm = simple_norm(data, stretch=stretch, percent=percent)

    # Plot and save
    plt.figure(figsize=(10, 10))
    plt.imshow(data, cmap=cmap, norm=norm, origin='lower')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(png_path, dpi=700, bbox_inches='tight', pad_inches=0)
    plt.close()

fits_to_png(fits_path=FILE_PREFIX+'assets/spt2_itermap_20120621_PLW.fits',
            png_path=FILE_PREFIX+'assets/spt2_itermap_20120621_PLW.png',
            cmap='cividis')

# Open PNG and convert to RGB (JPEG doesn't support transparency)
img = Image.open(FILE_PREFIX+'assets/spt2_itermap_20120621_PLW.png').convert("RGB")
img.save(FILE_PREFIX+'assets/spt2_itermap_20120621_PLW.jpg', "JPEG", quality=85)  # Adjust quality (85 is a good trade-off)