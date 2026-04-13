import base64
import json
import requests
from pyboy import PyBoy

class Input:
	def __init__(self, button: str, times: int = 1):
		self.button = button
		self.times = times

SECRETS: dict = json.load(open("secrets.json"))
SETTINGS: dict = json.load(open("settings.json"))
SERVER: str = SECRETS["server"]
MODEL: str = SECRETS["model"]
PROMPT: str = SETTINGS["prompt"]
ROM: str = SECRETS["rom"]
IMG_PATH: str = "tmp/screenshot.png"
TICKS_PER_INPUT: int = 360

input_queue = list[Input]()

def main():
	pyboy = PyBoy(ROM)
	pyboy.tick(600)
	while True:
		if len(input_queue) == 0:
			screenshot = pyboy.screen.image
			if screenshot:
				screenshot.save(IMG_PATH)
				print(summarize(IMG_PATH))
				process_input(input("> "))
			else:
				print("Screenshot failed!")
		if len(input_queue) > 0:
			current = input_queue[0]
			print("Pressing " + current.button)
			pyboy.button(current.button)
			current.times -= 1
			if current.times <= 0:
				input_queue.pop(0)
			pyboy.tick(TICKS_PER_INPUT)
		pass
	pyboy.stop()

def process_input(command: str):
	split = command.lower().split()
	if len(split) == 0:
		return
	button = split[0]
	times = 1
	if button not in ["up", "down", "left", "right", "a", "b", "start", "select"]:
		print("Invalid input: " + button)
		return
	elif len(split) > 1:
		try:
			times = int(split[1])
		except ValueError:
			pass
	input_queue.append(Input(button, times))

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
