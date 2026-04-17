import json
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont

JSON_PATH = "sprites.json"
TILES_FOLDER = "./tiles"
OUTPUT = "tiles.png"
TILE_SIZE = 16
PADDING = 4
SCALE = 2
TEXT_OFFSET = 8

SPRITES = json.load(open(JSON_PATH))["sprites"]


def main():
	tiles = []

	for sprite in SPRITES:
		row = sprite["row"]
		col = sprite["col"]
		description = sprite.get("description", "")
		tile = Image.open(f"{TILES_FOLDER}/{row}x{col}.png")
		tile = tile.resize((TILE_SIZE * SCALE, TILE_SIZE * SCALE), Image.Resampling.NEAREST)
		tiles.append((tile, description))

	# Draw the tiles in a single column, and next to each tile, write the description in a small font
	row_height = TILE_SIZE * SCALE + PADDING * 2
	canvas_height = row_height * len(tiles)
	canvas_width = 200
	canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 255))
	draw = ImageDraw.Draw(canvas)

	try:
		font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
	except OSError:
		font = ImageFont.load_default()

	for i, (tile, description) in enumerate(tiles):
		y = i * row_height + PADDING
		canvas.paste(tile, (PADDING, y))
		text_x = PADDING + TILE_SIZE * SCALE + TEXT_OFFSET
		text_y = y + (TILE_SIZE * SCALE) // 2 - 7
		draw.text((text_x, text_y), description, fill=(0, 0, 0, 255), font=font)

	canvas.save(OUTPUT)
	print(f"Saved {len(tiles)} tiles to {OUTPUT}")


if __name__ == "__main__":
	main()