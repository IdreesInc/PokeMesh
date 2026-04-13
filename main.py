import base64
import json
import requests
from pyboy import PyBoy

SECRETS: dict = json.load(open("secrets.json"))
SETTINGS: dict = json.load(open("settings.json"))
SERVER: str = SECRETS["server"]
MODEL: str = SECRETS["model"]
IMG_PATH: str = "tmp/screenshot.png"
PROMPT: str = SETTINGS["prompt"]

def main():
	pyboy = PyBoy("resources/yellow.gb")
	ticks: int = 0
	TRIGGER_COUNT: int = 1500
	while pyboy.tick():
		ticks += 1
		if ticks % TRIGGER_COUNT == 0:
			screenshot = pyboy.screen.image
			if screenshot:
				screenshot.save(IMG_PATH)
				print(summarize(IMG_PATH))
			else:
				print("Screenshot failed!")
		pass
	pyboy.stop()

def summarize(path: str) -> str:
	return request(PROMPT, path)

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
