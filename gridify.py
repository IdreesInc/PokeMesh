# Place a grid over an image
from PIL import Image, ImageDraw, ImageFont

TILE_SIZE = 9

def gridify(image_path: str, output_path: str, grid_size: int):
	image = Image.open(image_path)
	width, height = [x * 2 for x in image.size]
	grid_size *= 2
	image = image.resize((width, height), Image.Resampling.NEAREST)

	# Count the percentage of fully white pixels
	white_pixels = 0
	for pixel in image.getdata():
		if isinstance(pixel, (tuple, list)) and pixel[0] > 240 and pixel[1] > 240 and pixel[2] > 240:
			white_pixels += 1
	total_pixels = width * height
	white_percentage = white_pixels / total_pixels

	# Add one tile of padding to the left and bottom
	padded_width = width + grid_size
	padded_height = height + grid_size
	canvas = Image.new(image.mode, (padded_width, padded_height), 0)
	canvas.paste(image, (grid_size, 0))

	draw = ImageDraw.Draw(canvas)

	grid_offset_y = 8 * 2  # 8 pixels (scaled by 2x)

	if white_percentage < 0.5:
		for x in range(0, padded_width + 1, grid_size):
			draw.line([(x - 1, 0), (x - 1, padded_height)], fill="red", width=2)

		for y in range(grid_offset_y, padded_height + 1, grid_size):
			draw.line([(0, y - 1), (padded_width, y - 1)], fill="red", width=2)

	font = ImageFont.load_default(size=14)
	padding = 10
	for row in range(0, 9):
		draw.text((grid_size - padding, grid_offset_y + row * grid_size + padding), str(row), fill="white", font=font)
	for col in range(0, 15):
		draw.text(((col + 1) * grid_size + padding, height), str(col), fill="white", font=font)

	canvas.save(output_path)