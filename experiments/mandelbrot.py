import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import RectangleSelector
from numba import cuda

# --- Configuration ---
WIDTH, HEIGHT = 1200, 800
MAX_ITER = 256
THREADS_PER_BLOCK = (16, 16)


# --- CUDA Kernel ---
@cuda.jit
def mandelbrot_kernel(min_x, max_x, min_y, max_y, image, max_iter):
    height, width = image.shape
    x, y = cuda.grid(2)

    if x < width and y < height:
        # Map pixel to complex plane
        real_factor = (max_x - min_x) / (width - 1)
        imag_factor = (max_y - min_y) / (height - 1)

        c_real = min_x + x * real_factor
        c_imag = min_y + y * imag_factor

        z_real = 0.0
        z_imag = 0.0
        iter_count = 0

        # Optimized main loop (escape radius squared = 4.0)
        while (z_real * z_real + z_imag * z_imag <= 4.0) and (iter_count < max_iter):
            temp_real = z_real * z_real - z_imag * z_imag + c_real
            z_imag = 2.0 * z_real * z_imag + c_imag
            z_real = temp_real
            iter_count += 1

        image[y, x] = iter_count


class InteractiveMandelbrot:
    def __init__(self):
        # Initial Coordinates
        self.x_min, self.x_max = -2.5, 1.5
        self.y_min, self.y_max = -1.2, 1.2
        self.aspect_ratio_fix()

        # Initialize image
        self.image = np.zeros((HEIGHT, WIDTH), dtype=np.float32)

        # Setup Plot
        self.fig, self.ax = plt.subplots(figsize=(10, 7))

        try:
            self.fig.canvas.manager.set_window_title("GPU Mandelbrot")
        except AttributeError:
            pass

        colors = [
            (0.0, 0.0, 0.3),
            (0.0, 0.5, 1.0),
            (1.0, 1.0, 1.0),
            (1.0, 0.6, 0.0),
            (0.0, 0.0, 0.0),
        ]
        cmap = LinearSegmentedColormap.from_list("mandel_custom", colors, N=MAX_ITER)

        self.im = self.ax.imshow(
            self.image,
            origin="lower",
            cmap=cmap,
            norm=None,
            vmin=0,
            vmax=MAX_ITER,
            extent=(self.x_min, self.x_max, self.y_min, self.y_max),
        )

        self.ax.set_axis_off()

        # Connect Events
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)

        # Rectangle selector for drag-to-zoom
        self.selector = RectangleSelector(
            self.ax,
            self.on_select,
            useblit=True,
            button=[1],  # Left mouse button
            minspanx=5,
            minspany=5,
            spancoords="pixels",
            interactive=True,
        )

        print("Initial render...")
        self.update_image()
        print("Render complete. Displaying window.")
        print("\nControls:")
        print("  - Left-click and drag to select a zoom area.")
        print("  - Mouse wheel to zoom in/out from the cursor position.")
        plt.show()

    def aspect_ratio_fix(self):
        target_ratio = WIDTH / HEIGHT
        x_width = self.x_max - self.x_min
        y_height = self.y_max - self.y_min
        current_ratio = x_width / y_height

        if y_height == 0:
            return  # Avoid division by zero

        if current_ratio > target_ratio:
            target_height = x_width / target_ratio
            center_y = (self.y_min + self.y_max) / 2
            self.y_min = center_y - target_height / 2
            self.y_max = center_y + target_height / 2
        else:
            target_width = y_height * target_ratio
            center_x = (self.x_min + self.x_max) / 2
            self.x_min = center_x - target_width / 2
            self.x_max = center_x + target_width / 2

    def update_image(self):
        # Debounce rapid calls
        self.fig.canvas.toolbar.set_message("Rendering...")

        d_image = cuda.to_device(self.image)

        blockspergrid_x = int(math.ceil(WIDTH / THREADS_PER_BLOCK[0]))
        blockspergrid_y = int(math.ceil(HEIGHT / THREADS_PER_BLOCK[1]))
        blockspergrid = (blockspergrid_x, blockspergrid_y)

        mandelbrot_kernel[blockspergrid, THREADS_PER_BLOCK](
            self.x_min, self.x_max, self.y_min, self.y_max, d_image, MAX_ITER
        )

        cuda.synchronize()
        self.image = d_image.copy_to_host()

        self.im.set_data(self.image)
        self.im.set_extent((self.x_min, self.x_max, self.y_min, self.y_max))
        self.fig.canvas.draw_idle()
        self.fig.canvas.toolbar.set_message("")

    def on_select(self, eclick, erelease):
        """Callback for rectangle selection (drag-to-zoom)."""
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

        if x1 is None or y1 is None or x2 is None or y2 is None:
            return  # Ignore clicks outside the axes

        print(f"Zooming to rectangle: ({x1:.4f}, {y1:.4f}) to ({x2:.4f}, {y2:.4f})")

        self.x_min, self.x_max = sorted([x1, x2])
        self.y_min, self.y_max = sorted([y1, y2])

        self.aspect_ratio_fix()
        self.update_image()

    def on_scroll(self, event):
        """Callback for mouse wheel zoom."""
        if event.inaxes != self.ax:
            return

        mouse_x, mouse_y = event.xdata, event.ydata
        if (
            mouse_x is None or mouse_y is None
        ):  # Ignore scroll events outside the plot area
            return

        scale_factor = 0.8 if event.button == "up" else 1.25

        x_width = (self.x_max - self.x_min) * scale_factor
        y_height = (self.y_max - self.y_min) * scale_factor

        self.x_min = mouse_x - (mouse_x - self.x_min) * scale_factor
        self.x_max = self.x_min + x_width
        self.y_min = mouse_y - (mouse_y - self.y_min) * scale_factor
        self.y_max = self.y_min + y_height

        self.aspect_ratio_fix()
        self.update_image()


if __name__ == "__main__":
    if cuda.is_available():
        print(f"CUDA Device: {cuda.get_current_device().name}")
        app = InteractiveMandelbrot()
    else:
        print("No CUDA GPU found.")
