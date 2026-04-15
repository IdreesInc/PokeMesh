import threading
import asyncio
import base64
import json
import requests
from pyboy import PyBoy
from meshcore import MeshCore, EventType

class Input:
	def __init__(self, button: str, times: int = 1):
		self.button = button
		self.times = times

SECRETS: dict = json.load(open("secrets.json"))
SETTINGS: dict = json.load(open("settings.json"))
SERVER: str = SECRETS["server"]
SERVER_TOKEN: str = SECRETS["server_token"]
MODEL: str = SECRETS["model"]
PROMPT: str = SETTINGS["prompt"]
ROM: str = SECRETS["rom"]
IMG_PATH: str = "tmp/screenshot.png"
TICKS_PER_INPUT: int = 360
CHANNEL_IDX = SETTINGS["channel"]

input_queue = list[Input]()

def main():
	pyboy = PyBoy(ROM)
	pyboy.tick(600)
	input_thread = threading.Thread(target=input_loop)
	input_thread.start()
	meshcore_thread = threading.Thread(target=lambda: asyncio.run(connect_to_meshcore()), daemon=True)
	meshcore_thread.start()
	while pyboy.tick(1):
		if len(input_queue) > 0:
			current = input_queue[0]
			print("Pressing " + current.button)
			pyboy.button(current.button)
			current.times -= 1
			if current.times <= 0:
				input_queue.pop(0)
			pyboy.tick(TICKS_PER_INPUT)
			if len(input_queue) == 0:
				capture_and_summarize(pyboy)
	pyboy.stop()

async def connect_to_meshcore():
	meshcore = await MeshCore.create_serial("/dev/tty.usbmodem441BF66A71281")
	channel_info = await meshcore.commands.get_channel(CHANNEL_IDX)
	print(f"Listening to channel {channel_info.payload['channel_name']}...")
	await meshcore.start_auto_message_fetching()
	meshcore.subscribe(EventType.CHANNEL_MSG_RECV, handle_channel_message, attribute_filters={"channel_idx": CHANNEL_IDX})
	# Maintain thread indefinitely
	await asyncio.Future()

async def handle_channel_message(event):
	msg = event.payload or {}
	chan = msg.get("channel_idx")
	text = msg.get("text", "")
	path_len = msg.get("path_len")
	sender = text.split(":", 1)[0].strip()
	print(f"{text} > path_len={path_len}")
	process_input(text.split(":", 1)[1].strip())

def capture_and_summarize(pyboy: PyBoy):
	print("Capturing screenshot...")
	screenshot = pyboy.screen.image
	if screenshot:
		screenshot.save(IMG_PATH)
		print("Summarizing screenshot...")
		threading.Thread(target=lambda: print(summarize(IMG_PATH))).start()
	else:
		print("Screenshot failed!")

def input_loop():
	while True:
		process_input(input("> "))


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
		headers={
			"Authorization": f"Bearer {SERVER_TOKEN}"
		},
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