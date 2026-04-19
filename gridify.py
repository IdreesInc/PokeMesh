# Place a grid over an image
import os
from PIL import Image, ImageDraw, ImageFont

NAMED_TILES_DIR = "named_tiles"
REPLACEMENT_TILES_DIR = "replacement_tiles"
DOOR_TILE = "door.png"
TILE_SIZE = 9
ROW_INDEX_OFFSET = 4
COL_INDEX_OFFSET = 7
LINE_WIDTH = 2
GRID_OFFSET_Y = 8 * 2  # 8 pixels scaled by 2x
LABEL_PADDING = 15
DEBUG = True

def load_saved_tiles(directory: str) -> dict[str, Image.Image]:
	tiles: dict[str, Image.Image] = {}
	for filename in os.listdir(directory):
		if filename.endswith(".png"):
			name = os.path.splitext(filename)[0]
			path = os.path.join(directory, filename)
			tiles[name] = Image.open(path)
	return tiles

def compare_tiles(template: Image.Image, tile: Image.Image) -> bool:
	if template.size != tile.size:
		return False
	for x in range(template.width):
		for y in range(template.height):
			if template.getpixel((x, y)) != tile.getpixel((x, y)):
				return False
	return True

def gridify(image_path: str, output_path: str, grid_size: int):
	image = Image.open(image_path)
	width, height = image.width * 2, image.height * 2
	grid_size *= 2
	image = image.resize((width, height), Image.Resampling.NEAREST)
	
	named_tiles = load_saved_tiles(NAMED_TILES_DIR)
	replacement_tiles = load_saved_tiles(REPLACEMENT_TILES_DIR)

	# Padded canvas: one extra tile column on the left, one extra tile row on the bottom
	canvas = Image.new(image.mode, (width + grid_size, height + grid_size), 0)
	canvas.paste(image, (grid_size, 0))
	padded_w, padded_h = canvas.size

	x_slices = slice(padded_w, grid_size, grid_size)
	y_slices = slice(padded_h, GRID_OFFSET_Y, grid_size)

	xs = target_positions(x_slices, LINE_WIDTH)
	ys = target_positions(y_slices, LINE_WIDTH)

	new_w = sum(e - s for s, e in x_slices) + (len(x_slices) - 1) * LINE_WIDTH
	new_h = sum(e - s for s, e in y_slices) + (len(y_slices) - 1) * LINE_WIDTH
	out = Image.new(image.mode, (new_w, new_h), 0)

	debug_dir = None
	if DEBUG:
		debug_dir = os.path.join(os.path.dirname(output_path), "tiles")
		os.makedirs(debug_dir, exist_ok=True)

	for iy, (y0, y1) in enumerate(y_slices):
		for ix, (x0, x1) in enumerate(x_slices):
			tile = canvas.crop((x0, y0, x1, y1))
			for name, template in named_tiles.items():
				if compare_tiles(template, tile):
					print(f"Tile at ({ix}, {iy}) matches '{name}'")
					tile = replacement_tiles["door"]
			out.paste(tile, (xs[ix], ys[iy]))
			if DEBUG and debug_dir:
				tile.save(os.path.join(debug_dir, f"tile_{iy}_{ix}.png"))

	draw = ImageDraw.Draw(out)

	for ix in range(1, len(x_slices)):
		gx = xs[ix] - LINE_WIDTH
		draw.rectangle([(gx, 0), (gx + LINE_WIDTH - 1, new_h - 1)], fill="red")

	for iy in range(1, len(y_slices)):
		gy = ys[iy] - LINE_WIDTH
		draw.rectangle([(0, gy), (new_w - 1, gy + LINE_WIDTH - 1)], fill="red")

	font = ImageFont.load_default(size=14)

	def rx(v):
		return redraw(v, x_slices, xs)

	def ry(v):
		return redraw(v, y_slices, ys)

	for row in range(9):
		draw.text(
			(
				rx(grid_size - LABEL_PADDING),
				ry(GRID_OFFSET_Y + row * grid_size + LABEL_PADDING),
			),
			str(row - ROW_INDEX_OFFSET),
			fill="white",
			font=font,
		)
	for col in range(15):
		draw.text(
			(rx((col + 1) * grid_size + LABEL_PADDING), ry(height)),
			str(col - COL_INDEX_OFFSET),
			fill="white",
			font=font,
		)

	out.save(output_path)

def slice(total: int, offset: int, step: int) -> list[tuple[int, int]]:
	slices = [(0, offset)]
	pos = offset
	while pos < total:
		slices.append((pos, min(pos + step, total)))
		pos += step
	return slices


def target_positions(slices: list[tuple[int, int]], gap: int) -> list[int]:
	positions = []
	pos = 0
	for start, end in slices:
		positions.append(pos)
		pos += (end - start) + gap
	return positions


def redraw(coord: int, slices: list[tuple[int, int]], positions: list[int]) -> int:
	for i, (s, e) in enumerate(slices):
		if s <= coord < e:
			return positions[i] + (coord - s)
	return positions[-1] + (coord - slices[-1][0])