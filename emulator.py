import os
import requests

class Emulator:
	def __init__(self, url):
		self.url = url
		print("Initializing emulator...")

	def load_rom(self, path: str) -> None:
		path = os.path.abspath(path)
		ENDPOINT = self.url + "/core/loadfile"
		response = requests.post(ENDPOINT, params={"path": path})
		if response.status_code != 200:
			print("Failed to load ROM: " + response.text)
		else:
			print("Game loaded successfully!")

	def load_state(self, path: str) -> None:
		path = os.path.abspath(path)
		ENDPOINT = self.url + "/core/loadstatefile"
		response = requests.post(ENDPOINT, params={"path": path})
		if response.status_code != 200:
			print("Failed to load state: " + response.text)

	def save_state(self, file) -> None:
		path = os.path.abspath(file.name)
		ENDPOINT = self.url + "/core/savestatefile"
		response = requests.post(ENDPOINT, params={"path": path})
		if response.status_code != 200:
			print("Failed to save state: " + response.text)

	def press(self, button: str) -> None:
		ENDPOINT = self.url + "/mgba-http/button/tap"
		response = requests.post(ENDPOINT, params={"button": button.capitalize()})
		if response.status_code != 200:
			print("Failed to press button: " + response.text)

	def screenshot(self, path: str) -> None:
		path = os.path.abspath(path)
		ENDPOINT = self.url + "/core/screenshot"
		response = requests.post(ENDPOINT, params={"path": path})
		if response.status_code != 200:
			print("Failed to capture screenshot: " + response.text)