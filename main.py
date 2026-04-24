import os
import threading
import asyncio
import time
import json
import random
from typing import NoReturn
from meshcore import MeshCore, EventType
from emulator import Emulator
from preprocessor import preprocess
from stats import Stats
from summarizer import Summarizer
from game_data import MAP_NAMES

class Action:
	VALID_BUTTONS = ["up", "down", "left", "right", "a", "b", "start", "select", "random"]
	
	def __init__(self, button: str, times: int = 1):
		self.button = button
		self.times = times

class Query:
	VALID_QUERIES = ["help", "about", "where", "ping", "source", "example", "leaderboard"]

	def __init__(self, action: str, value: str) -> None:
		self.action = action
		self.value = value

SECRETS: dict = json.load(open("secrets.json"))
SETTINGS: dict = json.load(open("settings.json"))
SERVER: str = SECRETS["server"]
SERVER_TOKEN: str = SECRETS["server_token"]
MGBA_URL: str = SECRETS["mgba_url"]
USB_SERIAL: str = SECRETS["usb_serial"]
MODEL: str = SETTINGS["model"]
PROMPT: str = "\n".join(SETTINGS["prompt"])
EMULATION_SPEED: float = SETTINGS["emulation_speed"]
MAX_TIMES: int = SETTINGS["max_inputs"]
TIME_BETWEEN_ROUNDS: float = SETTINGS["time_between_rounds"]
PREFIXES: list[str] = SETTINGS["prefixes"]
LOCAL: bool = SECRETS.get("local", False)

IMG_PATH: str = "tmp/screenshot.png"
MODIFIED_IMG_PATH: str = "tmp/screenshot_grid.png"
SECONDS_PER_INPUT: float = 0.5 / EMULATION_SPEED
SECONDS_BEFORE_SUMMARY: float = 4.0 / EMULATION_SPEED
CHANNEL_IDX = SETTINGS["channel"]
SAVE_STATE_DIRECTORY = "data/saves"
RANDOM_BUTTONS = ["up", "down", "left", "right"]

summarizer = Summarizer(SECRETS, SETTINGS)
stats = Stats("stats.json")
input_queue = list[Action|Query]()
output_queue = list[str]()
# Map of users to requested inputs
input_requests: dict[str, list[Action]] = {}
round_end_time = 0.0
bonk_counter = 0

def main():
	global round_end_time
	emulator = Emulator(MGBA_URL)
	load_state(emulator)
	input_thread = threading.Thread(target=input_loop)
	input_thread.start()
	meshcore_thread = threading.Thread(target=lambda: asyncio.run(connect_to_meshcore()), daemon=True)
	meshcore_thread.start()
	bonk_thread = threading.Thread(target=lambda: asyncio.run(bonk_loop(emulator)), daemon=True)
	bonk_thread.start()
	bonks_at_start = 0
	previous_location = None
	while True:
		if len(input_queue) > 0:
			if isinstance(input_queue[0], Action):
				current = input_queue[0]
				print("Pressing " + current.button)
				if current.button == "random":
					random_button = random.choice(RANDOM_BUTTONS)
					print("Randomly pressing " + random_button)
					emulator.press(random_button)
				else:
					emulator.press(current.button)
				stats.increment_buttons_pressed()
				current.times -= 1
				if current.times <= 0:
					input_queue.pop(0)
				time.sleep(SECONDS_PER_INPUT)
				if len(input_queue) == 0:
					if bonk_counter > bonks_at_start:
						bonk_amount = bonk_counter - bonks_at_start
						stats.increment_bonks(bonk_amount)
						output(f"Detected {bonk_amount} bonk{'' if bonk_amount == 1 else 's'}")
					time.sleep(SECONDS_BEFORE_SUMMARY)
					save_state(emulator)
					stats.increment_rounds()
					location = get_location(emulator)
					if location != previous_location:
						stats.increment_visited_location(location)
						print(f"Location changed: {location}")
						previous_location = location
					stats.save()
					capture_and_summarize(emulator)
			elif isinstance(input_queue[0], Query):
				query = input_queue[0]
				print("Processing query: " + query.action)
				if query.action == "help":
					output("Queries: " + ", ".join(Query.VALID_QUERIES) + "\nInputs: " + ", ".join(Action.VALID_BUTTONS))
				elif query.action == "about":
					output("PokeMesh is a collaborative game of Pokémon FireRed! Players submit inputs and the most requested inputs are ran every " + str(int(TIME_BETWEEN_ROUNDS)) + "s.")
					output("Type '/poke example' for input examples or '/poke source' for more info on how it works")
				elif query.action == "where" or query.action == "location":
					output(f"Location: {get_location(emulator)}")
				elif query.action == "ping":
					output("Pong!")
				elif query.action == "source" or query.action == "who":
					output("PokeMesh was created by Idrees, check out the code at https://github.com/IdreesInc/PokeMesh")
				elif query.action == "example":
					output("Example input: '/poke up 2 right a 3' will press 'up' twice, then 'right' once, then 'a' three times")
				elif query.action == "leaderboard":
					leaderboard = stats.get_leaderboard()
					output("Leaderboard:\n" + "\n".join(": ".join(str(i) for i in stat) for stat in leaderboard))
				input_queue.pop(0)
		elif time.time() > round_end_time:
			print("Round ended. Processing input requests...")
			bonks_at_start = bonk_counter
			# Map of input sequence hashes to number of requests for that sequence
			unique_requests: dict[tuple[tuple[str, int], ...], int] = {}
			most_requested = None
			max_requests = 0
			for user, sequence in input_requests.items():
				hashable = tuple((request.button, request.times) for request in sequence)
				unique_requests[hashable] = unique_requests.get(hashable, 0) + 1
				if unique_requests[hashable] > max_requests:
					max_requests = unique_requests[hashable]
					most_requested = sequence
			if most_requested:
				input_queue.extend(most_requested)
				output("Pressing buttons with " + str(max_requests) + f" vote{'' if max_requests == 1 else 's'}: " + ", ".join(f"{action.button} {action.times}" for action in most_requested))
			else:
				print("No inputs requested this round")
			input_requests.clear()
			# Set extended time just in case summary fails
			round_end_time = time.time() + TIME_BETWEEN_ROUNDS * 3
		time.sleep(0.1)

async def bonk_loop(emulator: Emulator) -> NoReturn:
	global bonk_counter
	last_bonk = None
	while True:
		bonk = emulator.read_address(0x03002518) == 0xB6
		if bonk != last_bonk:
			if bonk:
				print("Bonk")
				bonk_counter += 1
			last_bonk = bonk
		await asyncio.sleep(0.1)

def load_state(emulator: Emulator) -> None:
	save_files = [f for f in os.listdir(SAVE_STATE_DIRECTORY) if f.endswith(".ss1")]
	if not save_files:
		print("No save state found, starting fresh.")
		return
	save_files.sort(reverse=True)
	path = os.path.join(SAVE_STATE_DIRECTORY, save_files[0])
	emulator.load_state(path)

def save_state(emulator: Emulator) -> None:
	with open(os.path.join(SAVE_STATE_DIRECTORY, f"save_{epoch_time()}.ss1"), "wb") as f:
		emulator.save_state(f)

async def connect_to_meshcore() -> NoReturn:
	meshcore = await MeshCore.create_serial(USB_SERIAL)
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
	full_text = msg.get("text", "")
	path_len = msg.get("path_len")
	sender = full_text.split(":", 1)[0].strip()
	text = full_text.split(":", 1)[1].strip()
	print(f"[{sender}]: {text} > channel {chan}, path_len={path_len}")
	if chan == CHANNEL_IDX:
		for prefix in PREFIXES:
			if text.startswith(prefix):
				text = text[len(prefix):].strip()
				process_input(text, sender)
				stats.increment_user_action(sender)
				break

async def send_message(meshcore: MeshCore, text: str):
	await meshcore.commands.send_chan_msg(CHANNEL_IDX, text)

def capture_and_summarize(emulator: Emulator):
	print("Capturing screenshot...")
	# screenshot = pyboy.screen.image
	emulator.screenshot(IMG_PATH)
	matches = preprocess(IMG_PATH, MODIFIED_IMG_PATH, 16)
	print("Summarizing screenshot...")
	threading.Thread(target=lambda: output_summary(summarizer.summarize(MODIFIED_IMG_PATH, matches))).start()

def output_summary(summary: str):
	global round_end_time
	output(summary)
	round_end_time = time.time() + TIME_BETWEEN_ROUNDS

def input_loop():
	while True:
		process_input(input("> "))

def output(message: str):
	print(message)
	if not LOCAL:
		output_queue.append(message)

def process_input(command: str, sender: str | None = None):
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
			if sender is not None:
				input_requests[sender] = new_inputs
				print(f"{sender} has requested " + ", ".join(f"{action.button} {action.times}" for action in new_inputs))
			else:
				input_queue.extend(new_inputs)
	elif command in Query.VALID_QUERIES:
		input_queue.append(Query(command, ""))
	else:
		output("Unknown command: " + command)

def get_location(emulator: Emulator) -> str:
	bank = emulator.read_address(0x02031DBC)
	map_num = emulator.read_address(0x02031DBD)
	return MAP_NAMES.get((bank, map_num), f"Unknown with bank={bank:#04x}, map={map_num:#04x}")

def epoch_time() -> int:
	return int(time.time())

if __name__ == "__main__":
	main()