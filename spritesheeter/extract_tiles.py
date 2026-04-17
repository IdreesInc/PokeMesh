import PIL.Image as Image
import pathlib

SPRITE_SHEET_PATH = "spritesheet.png"
OUTPUT_DIR = "tiles"
TILE_SIZE = 16

def main():
	spritesheet = Image.open(SPRITE_SHEET_PATH)
	sheet_width, sheet_height = spritesheet.size
	cols = sheet_width // TILE_SIZE
	rows = sheet_height // TILE_SIZE

	out = pathlib.Path(OUTPUT_DIR)
	out.mkdir(exist_ok=True)

	saved = 0
	for row in range(rows):
		for col in range(cols):
			tile = spritesheet.crop((
				col * TILE_SIZE,
				row * TILE_SIZE,
				(col + 1) * TILE_SIZE,
				(row + 1) * TILE_SIZE,
			))
			colors = tile.convert("RGBA").getcolors(TILE_SIZE * TILE_SIZE)
			if colors and len(colors) == 1:
				continue
			tile.save(out / f"{row}x{col}.png")
			saved += 1

	print(f"Extracted {saved} non-empty tiles to '{OUTPUT_DIR}/'")

if __name__ == "__main__":
	main()
