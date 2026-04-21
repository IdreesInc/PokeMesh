import os
from PIL import Image, ImageDraw, ImageFont

NAMED_TILES_DIR = "named_tiles"
REPLACEMENT_TILES_DIR = "replacement_tiles"
ROW_INDEX_OFFSET = 4
COL_INDEX_OFFSET = 7
LINE_WIDTH = 2
GRID_OFFSET_Y = 8 * 2
FUZZY_MATCH_THRESHOLD = 0.8
COLOR_DISTANCE_THRESHOLD = 30
PROMPT_TILES = {
	"cuttabletree": "cuttable tree",
	"door": "door",
	"doorup": "door",
	"doordown": "door",
	"ladderup": "ladder going up",
	"ladderdown": "ladder going down",
	"item": "item",
}
DEBUG = True


def load_saved_tiles(directory: str) -> dict[str, Image.Image]:
	tiles: dict[str, Image.Image] = {}
	for filename in os.listdir(directory):
		if filename.endswith(".png"):
			name = os.path.splitext(filename)[0]
			path = os.path.join(directory, filename)
			tiles[name] = Image.open(path)
	return tiles


def color_distance(colorA, colorB) -> float:
	if isinstance(colorA, int):
		colorA = (colorA,)
	if isinstance(colorB, int):
		colorB = (colorB,)
	return sum((a - b) ** 2 for a, b in zip(colorA, colorB)) ** 0.5


def compare_tiles(template: Image.Image, tile: Image.Image) -> float:
	if template.size != tile.size:
		return 0.0
	total_pixels: int = 0
	matched_pixels: int = 0
	for x in range(template.width):
		for y in range(template.height):
			pixel = template.getpixel((x, y))
			if color_distance(pixel, 0) <= COLOR_DISTANCE_THRESHOLD:
				# Ignore black pixels in the template
				continue
			total_pixels += 1
			if color_distance(pixel, tile.getpixel((x, y))) <= COLOR_DISTANCE_THRESHOLD:
				matched_pixels += 1
	return matched_pixels / total_pixels if total_pixels > 0 else 0.0


def tile_slice(total: int, offset: int, step: int) -> list[tuple[int, int]]:
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


def preprocess(image_path: str, output_path: str, tile_size: int) -> dict[str, str]:
	orig_image = Image.open(image_path)
	orig_tile_size = tile_size

	scaled_tile_size = tile_size * 2
	scaled_image = orig_image.resize(
		(orig_image.width * 2, orig_image.height * 2),
		Image.Resampling.NEAREST,
	)

	named_tiles = load_saved_tiles(NAMED_TILES_DIR)
	replacement_tiles = load_saved_tiles(REPLACEMENT_TILES_DIR)

	orig_w, orig_h = orig_image.size
	orig_canvas = Image.new(orig_image.mode, (orig_w + orig_tile_size, orig_h + orig_tile_size), 0)
	orig_canvas.paste(orig_image, (orig_tile_size, 0))
	orig_x_slices = tile_slice(orig_w + orig_tile_size, orig_tile_size, orig_tile_size)
	orig_y_slices = tile_slice(orig_h + orig_tile_size, GRID_OFFSET_Y // 2, orig_tile_size)

	# Scale named tiles down for comparison
	compare_named_tiles = {
		name: template.resize((orig_tile_size, orig_tile_size), Image.Resampling.NEAREST)
		for name, template in named_tiles.items()
	}

	scaled_w, scaled_h = scaled_image.size
	canvas = Image.new(scaled_image.mode, (scaled_w + scaled_tile_size, scaled_h + scaled_tile_size), 0)
	canvas.paste(scaled_image, (scaled_tile_size, 0))
	padded_w, padded_h = canvas.size

	x_slices = tile_slice(padded_w, scaled_tile_size, scaled_tile_size)
	y_slices = tile_slice(padded_h, GRID_OFFSET_Y, scaled_tile_size)

	xs = target_positions(x_slices, LINE_WIDTH)
	ys = target_positions(y_slices, LINE_WIDTH)

	new_w = sum(e - s for s, e in x_slices) + (len(x_slices) - 1) * LINE_WIDTH
	new_h = sum(e - s for s, e in y_slices) + (len(y_slices) - 1) * LINE_WIDTH
	out = Image.new(scaled_image.mode, (new_w, new_h), 0)

	debug_dir = None
	if DEBUG:
		debug_dir = os.path.join(os.path.dirname(output_path), "tiles")
		os.makedirs(debug_dir, exist_ok=True)

	matches: dict[str, str] = {}

	for iy, (y0, y1) in enumerate(y_slices):
		for ix, (x0, x1) in enumerate(x_slices):
			tile = canvas.crop((x0, y0, x1, y1))
			if DEBUG and debug_dir:
				tile.save(os.path.join(debug_dir, f"tile_{iy}_{ix}.png"))

			# Compare at original resolution to avoid redundant work
			oy0, oy1 = orig_y_slices[iy]
			ox0, ox1 = orig_x_slices[ix]
			compare_tile = orig_canvas.crop((ox0, oy0, ox1, oy1))
			best_name, best_match = None, FUZZY_MATCH_THRESHOLD
			for name, template in compare_named_tiles.items():
				match = compare_tiles(template, compare_tile)
				if match > best_match:
					best_name, best_match = name, match

			if best_name is not None:
				col_coord = (ix - 1) - COL_INDEX_OFFSET
				row_coord = ROW_INDEX_OFFSET - (iy - 1)
				if DEBUG:
					print(f"Tile at ({col_coord}, {row_coord}) matches '{best_name}' with {best_match:.2%} similarity")
				horizontal = "tiles right" if col_coord >= 0 else "tiles left"
				vertical = "tiles up" if row_coord >= 0 else "tiles down"
				template_name = best_name.split("_")[-1]
				tile = replacement_tiles.get(template_name, tile)
				if template_name in PROMPT_TILES:
					matches[f"{ix},{iy}"] = f"({abs(col_coord)} {horizontal}, {abs(row_coord)} {vertical}) -> {PROMPT_TILES[template_name]}"

			out.paste(tile, (xs[ix], ys[iy]))

	if DEBUG:
		print("\n".join(matches.values()))

	draw = ImageDraw.Draw(out)
	font = ImageFont.load_default(size=14)
	small_font = ImageFont.load_default(size=11)

	for ix in range(1, len(x_slices)):
		gx = xs[ix] - LINE_WIDTH
		draw.rectangle([(gx, 0), (gx + LINE_WIDTH - 1, new_h - 1)], fill="red")

	for iy in range(1, len(y_slices) - 1):
		gy = ys[iy] - LINE_WIDTH
		draw.rectangle([(0, gy), (new_w - 1, gy + LINE_WIDTH - 1)], fill="red")

	def rx(v):
		return redraw(v, x_slices, xs)

	def ry(v):
		return redraw(v, y_slices, ys)

	for row in range(9):
		row_val = (row - ROW_INDEX_OFFSET) * -1
		direction = "up" if row_val > 0 else ("down" if row_val < 0 else "")
		cx = rx(scaled_tile_size // 2)
		cy = ry(GRID_OFFSET_Y + row * scaled_tile_size + scaled_tile_size // 2)
		draw.text((cx, cy - 7), str(row_val), fill="white", font=font, anchor="mm")
		if direction:
			draw.text((cx, cy + 7), direction, fill="white", font=small_font, anchor="mm")

	for col in range(15):
		col_val = col - COL_INDEX_OFFSET
		direction = "right" if col_val > 0 else ("left" if col_val < 0 else "")
		cx = rx((col + 1) * scaled_tile_size + scaled_tile_size // 2)
		cy = ry(scaled_h + scaled_tile_size // 2)
		draw.text((cx, cy - 7), str(col_val), fill="white", font=font, anchor="mm")
		if direction:
			draw.text((cx, cy + 7), direction, fill="white", font=small_font, anchor="mm")

	out.save(output_path)
	return matches
