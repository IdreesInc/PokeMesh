import base64
import json
import requests
from pyboy import PyBoy

SETTINGS: dict = json.load(open("settings.json"))
SERVER: str = SETTINGS["server"]
MODEL: str = SETTINGS["model"]
IMG_PATH: str = "tmp/screenshot.png"

def main():
	pyboy = PyBoy("resources/yellow.gb")
	ticks: int = 0
	MAX_TICKS: int = 1500
	while pyboy.tick():
		ticks += 1
		if ticks == MAX_TICKS:
			screenshot = pyboy.screen.image
			if screenshot:
				screenshot.save(IMG_PATH)
				print(summarize(IMG_PATH))
			else:
				print("Screenshot failed!")
			break
		pass
	pyboy.stop()

def summarize(path: str) -> str:
	return request("Briefly, what's happening in this image?", path)

def request(message: str, image_path: str | None) -> str:
	content: list = [
		{
			"type": "text",
			"text": message
		}
	]
	if image_path:
		with open(image_path, "rb") as f:
			encoded = base64.b64encode(f.read()).decode("utf-8")
			content.append({
				"type": "image_url",
				"image_url": {
					"url": "data:image/png;base64," + encoded
				}
			})

	response = requests.post(
		"http://" + SERVER + "/v1/chat/completions",
		json={
			"model": MODEL,
			"messages": [
				{
					"role": "user",
					"content": content
				}
			]
		}
	)
	return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
	main()
