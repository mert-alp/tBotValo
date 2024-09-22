from PIL import Image

# Set image dimensions (e.g., 1920x1080 for full HD)
width, height = 1920, 1080

# Set the hex color (e.g., "#FF0000" for red)
hex_color = "#FE8EFE"

# Convert hex to RGB
rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

# Create an image with the given color
image = Image.new("RGB", (width, height), rgb_color)

# Save the image
image.save("solid_color.png")