import os
import glob
import subprocess
import time

# Paths
DNG_PATH = "/media/RAW/CINEPI_25-02-08_184201_C00000"
TEMP_DIR = "/dev/shm/thumbnails"  # Store in RAM
os.makedirs(TEMP_DIR, exist_ok=True)

# Get framebuffer resolution
fb_res = subprocess.check_output("fbset | grep 'geometry'", shell=True).decode()
_, width, height, *_ = fb_res.split()
width, height = int(width), int(height)
print(f"Detected framebuffer resolution: {width}x{height}")

# Get sorted DNG files
dng_files = sorted(glob.glob(f"{DNG_PATH}/*.dng"))

if not dng_files:
    print("No DNG files found!")
    exit()

# Step 1: Convert DNG to Grayscale JPEG
jpeg_paths = []
for dng in dng_files:
    jpeg_path = os.path.join(TEMP_DIR, os.path.basename(dng).replace(".dng", "_grayscale.jpg"))
    jpeg_paths.append(jpeg_path)

    if not os.path.exists(jpeg_path):
        print(f"Generating Grayscale JPEG for {dng}...")
        subprocess.run(["dcraw", "-w", "-T", "-h", dng])  # Generate TIFF preview
        temp_tiff = dng.replace(".dng", ".tiff")

        if os.path.exists(temp_tiff):
            subprocess.run([
                "convert", temp_tiff, "-colorspace", "Gray", "-resize", f"{width}x{height}", jpeg_path
            ])  # Convert to Grayscale JPEG
            os.remove(temp_tiff)  # Clean up
        else:
            print(f"Failed to generate JPEG for {dng}")
            continue

# Step 2: Preload grayscale RGB565 frames into memory
print("Converting grayscale images to raw framebuffer format...")
raw_frames = []

for frame, image in enumerate(jpeg_paths):
    print(f"Processing frame {frame + 1}/{len(jpeg_paths)}: {image}")

    # Convert grayscale JPEG to raw RGB565
    raw_frame = subprocess.run([
        "ffmpeg", "-v", "quiet", "-y", "-i", image,
        "-f", "rawvideo", "-pix_fmt", "rgb565", "-s", f"{width}x{height}", "-"
    ], stdout=subprocess.PIPE).stdout

    if raw_frame:
        raw_frames.append(raw_frame)
    else:
        print(f"Failed to convert {image}, skipping.")

if not raw_frames:
    print("No frames converted, exiting.")
    exit()

print(f"Loaded {len(raw_frames)} frames into memory. Starting playback... Press Ctrl+C to stop.")

# Step 3: Playback Loop (FAST)
try:
    frame_time = 1 / 24  # Target 24 FPS
    last_time = time.perf_counter()

    for frame_idx, raw_frame in enumerate(raw_frames):
        print(f"Displaying frame {frame_idx + 1}/{len(raw_frames)}")

        # Send preconverted raw data to framebuffer
        with open("/dev/fb0", "wb") as fb:
            fb.write(raw_frame)

        # Frame timing
        while (time.perf_counter() - last_time) < frame_time:
            pass  # Wait for the correct frame duration
        last_time = time.perf_counter()

except KeyboardInterrupt:
    print("Exiting playback...")
