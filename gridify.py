# Place a grid over an image
from PIL import Image, ImageDraw

def gridify(image_path: str, output_path: str, grid_size: int):
	image = Image.open(image_path).convert("L").convert("RGBA")
	width, height = [x * 2 for x in image.size]
	grid_size *= 2
	image = image.resize((width , height), Image.Resampling.NEAREST)
	draw = ImageDraw.Draw(image)

	for x in range(0, width + 1, grid_size):
		draw.line([(x - 1, 0), (x - 1, height)], fill="red", width=2)

	for y in range(0, height + 1, grid_size):
		draw.line([(0, y - 1), (width, y - 1)], fill="red", width=2)

	image.save(output_path)