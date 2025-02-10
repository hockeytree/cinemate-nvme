import numpy as np
import mmap
import os

# Define framebuffer resolution
fb_width, fb_height = 1920, 1080
fb_stride = fb_width * 2  # Each pixel is 2 bytes (RGB565)
fb_size = fb_stride * fb_height  # Total framebuffer size

# Additional logging for framebuffer size
print(f"Framebuffer resolution: {fb_width}x{fb_height}")
print(f"Framebuffer size (in bytes): {fb_size}")

# Check if framebuffer exists
if not os.path.exists("/dev/fb0"):
    print("Error: Framebuffer device /dev/fb0 not found!")
    exit()

# Open framebuffer for memory-mapped access
with open("/dev/fb0", "r+b") as fb:
    fb_mem = mmap.mmap(fb.fileno(), fb_size, mmap.MAP_SHARED, mmap.PROT_WRITE)

    print("Framebuffer opened successfully.")

    # Generate a test image (gradient)
    print("Generating test gradient...")
    test_image = np.linspace(0, 0xFFFF, num=fb_width * fb_height, dtype=np.uint16).reshape(fb_height, fb_width)

    # Validate the test image (checking min, max, and mean)
    print(f"Test image: Min={np.min(test_image)}, Max={np.max(test_image)}, Mean={np.mean(test_image)}")
    
    # Ensure proper row alignment by padding (if necessary)
    aligned_frame = np.zeros((fb_height, fb_stride // 2), dtype=np.uint16)  # Create padded buffer

    print("Aligning frame buffer...")

    # Copy image into aligned buffer
    aligned_frame[:, :fb_width] = test_image

    # Check the shape of the aligned frame
    print(f"Aligned frame shape: {aligned_frame.shape}")

    # Convert to bytes and write to framebuffer
    try:
        fb_mem.seek(0)
        fb_mem.write(aligned_frame.tobytes())
        fb_mem.flush()
        print("Test gradient written to framebuffer successfully.")
    except Exception as e:
        print(f"Error writing to framebuffer: {e}")
        fb_mem.close()
        exit()

    # Check if the framebuffer contents are consistent
    fb_mem.seek(0)
    test_data = fb_mem.read(fb_size)

    if test_data:
        print(f"Framebuffer data read successfully: {len(test_data)} bytes.")
    else:
        print("Error: Unable to read framebuffer data.")

    print("Displayed test gradient. Check if it's full-screen.")

    # Wait for user input before exiting
    input("Press Enter to exit.")
    fb_mem.close()

    print("Framebuffer memory closed.")
