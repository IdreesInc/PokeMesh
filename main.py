import os
import threading
import asyncio
import time
import json
from typing import NoReturn
from pyboy import PyBoy
from meshcore import MeshCore, EventType
from gridify import gridify
from summarizer import Summarizer
from game_data import Locations

class Action:
	VALID_BUTTONS = ["up", "down", "left", "right", "a", "b", "start", "select"]
	
	def __init__(self, button: str, times: int = 1):
		self.button = button
		self.times = times

class Query:
	VALID_QUERIES = ["help", "summarize", "where", "coordinates"]

	def __init__(self, action: str, value: str) -> None:
		self.action = action
		self.value = value

SECRETS: dict = json.load(open("secrets.json"))
SETTINGS: dict = json.load(open("settings.json"))
SERVER: str = SECRETS["server"]
SERVER_TOKEN: str = SECRETS["server_token"]
MODEL: str = SETTINGS["model"]
PROMPT: str = "\n".join(SETTINGS["prompt"])
ROM: str = SECRETS["rom"]
IMG_PATH: str = "tmp/screenshot.png"
MODIFIED_IMG_PATH: str = "tmp/screenshot_grid.png"
TICKS_PER_INPUT: int = 360
TICKS_BEFORE_SUMMARY: int = 360
CHANNEL_IDX = SETTINGS["channel"]
SAVE_STATE_DIRECTORY = "resources/saves"
MAX_TIMES = 10

summarizer = Summarizer(SECRETS, SETTINGS)
input_queue = list[Action|Query]()
output_queue = list[str]()

def main():
	pyboy = PyBoy(ROM)
	load_state(pyboy)
	pyboy.tick(600)
	input_thread = threading.Thread(target=input_loop)
	input_thread.start()
	meshcore_thread = threading.Thread(target=lambda: asyncio.run(connect_to_meshcore()), daemon=True)
	meshcore_thread.start()
	while pyboy.tick(1):
		if len(input_queue) > 0:
			if isinstance(input_queue[0], Action):
				current = input_queue[0]
				print("Pressing " + current.button)
				pyboy.button(current.button)
				current.times -= 1
				if current.times <= 0:
					input_queue.pop(0)
				pyboy.tick(TICKS_PER_INPUT)
				if len(input_queue) == 0:
					pyboy.tick(TICKS_BEFORE_SUMMARY)
					save_state(pyboy)
					capture_and_summarize(pyboy)
			elif isinstance(input_queue[0], Query):
				query = input_queue[0]
				print("Processing query: " + query.action)
				if query.action == "help":
					output("Commands: " + ", ".join(Query.VALID_QUERIES) + "\nInputs: " + ", ".join(Action.VALID_BUTTONS))
				elif query.action == "summarize":
					capture_and_summarize(pyboy)
				elif query.action == "where" or query.action == "location":
					location = get_location(pyboy)
					output(f"Location: {location}")
				elif query.action == "coordinates" or query.action == "coords":
					coords = get_coordinates(pyboy)
					output(f"Coordinates: {coords[0]}, {coords[1]}")
				input_queue.pop(0)
	pyboy.stop()

def load_state(pyboy: PyBoy) -> None:
	save_files = [f for f in os.listdir(SAVE_STATE_DIRECTORY) if f.endswith(".state")]
	if not save_files:
		print("No save state found, starting fresh.")
		return
	save_files.sort(reverse=True)
	with open(os.path.join(SAVE_STATE_DIRECTORY, save_files[0]), "rb") as f:
		pyboy.load_state(f)

def save_state(pyboy: PyBoy) -> None:
	with open(os.path.join(SAVE_STATE_DIRECTORY, f"save_{epoch_time()}.state"), "wb") as f:
		pyboy.save_state(f)

async def connect_to_meshcore() -> NoReturn:
	meshcore = await MeshCore.create_serial("/dev/tty.usbmodem441BF66A71281")
	channel_info = await meshcore.commands.get_channel(CHANNEL_IDX)
	print(f"Listening to channel {channel_info.payload['channel_name']}...")
	await meshcore.start_auto_message_fetching()
	meshcore.subscribe(EventType.CHANNEL_MSG_RECV, handle_message, attribute_filters={"channel_idx": CHANNEL_IDX})
	while True:
		if len(output_queue) > 0:
			message = output_queue.pop(0)
			await send_message(meshcore, message)
		await asyncio.sleep(0.1)

async def handle_message(event):
	msg = event.payload or {}
	chan = msg.get("channel_idx")
	text = msg.get("text", "")
	path_len = msg.get("path_len")
	sender = text.split(":", 1)[0].strip()
	print(f"{text} > channel {chan}, path_len={path_len}")
	process_input(text.split(":", 1)[1].strip())

async def send_message(meshcore: MeshCore, text: str):
	await meshcore.commands.send_chan_msg(CHANNEL_IDX, text)

def capture_and_summarize(pyboy: PyBoy):
	print("Capturing screenshot...")
	screenshot = pyboy.screen.image
	if screenshot:
		screenshot.save(IMG_PATH)
		gridify(IMG_PATH, MODIFIED_IMG_PATH, 16)
		print("Summarizing screenshot...")
		threading.Thread(target=lambda: output(summarizer.summarize(MODIFIED_IMG_PATH))).start()
	else:
		print("Screenshot failed!")

def input_loop():
	while True:
		process_input(input("> "))

def output(message: str):
	print(message)
	output_queue.append(message)

def process_input(command: str):
	split = command.lower().split()
	if len(split) == 0:
		return
	command = split[0]
	if command in Action.VALID_BUTTONS:
		index = 0
		new_inputs = []
		total_times = 0
		while index < len(split):
			if split[index] in Action.VALID_BUTTONS:
				button = split[index]
				index += 1
				times = 1
				if index < len(split) and split[index].isdigit():
					times = int(split[index])
					index += 1
				total_times += times
				new_inputs.append(Action(button, times))
			else:
				output("Unknown input: " + split[index])
				index += 1
		if total_times > MAX_TIMES:
			output(f"Too many inputs at once: {total_times} > {MAX_TIMES}")
		else:
			input_queue.extend(new_inputs)
	elif command in Query.VALID_QUERIES:
		input_queue.append(Query(command, ""))
	else:
		output("Unknown command: " + command)

def get_location(pyboy: PyBoy) -> str:
	MAP_ADDRESS = 0xD35E
	id = pyboy.memory[MAP_ADDRESS]
	return Locations.get(id, "Unknown Location")

def get_coordinates(pyboy: PyBoy) -> tuple[int, int]:
	X_ADDRESS = 0xD361
	Y_ADDRESS = 0xD362
	return (pyboy.memory[Y_ADDRESS], pyboy.memory[X_ADDRESS])

def epoch_time() -> int:
	return int(time.time())

if __name__ == "__main__":
	main()