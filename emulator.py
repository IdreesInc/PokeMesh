import os
import requests

class Emulator:
	def __init__(self, url):
		self.url = url
		print("Initializing emulator...")

	def load_state(self, path: str) -> None:
		path = os.path.abspath(path)
		print("Loading state from " + path + "...")
		ENDPOINT = self.url + "/core/loadstatefile"
		response = requests.post(ENDPOINT, params={"path": path})
		if response.status_code != 200:
			print("Failed to load state: " + response.text)
		else:
			print("State loaded successfully.")

	def save_state(self, file) -> None:
		path = os.path.abspath(file.name)
		print("Saving state to " + path + "...")
		ENDPOINT = self.url + "/core/savestatefile"
		response = requests.post(ENDPOINT, params={"path": path})
		if response.status_code != 200:
			print("Failed to save state: " + response.text)
		else:
			print("State saved successfully.")

	def press(self, button: str) -> None:
		print("Pressing " + button + "...")
		ENDPOINT = self.url + "/mgba-http/button/tap"
		response = requests.post(ENDPOINT, params={"button": button.capitalize()})

	def screenshot(self, path: str) -> None:
		path = os.path.abspath(path)
		print("Capturing screenshot to " + path + "...")
		ENDPOINT = self.url + "/core/screenshot"
		response = requests.post(ENDPOINT, params={"path": path})
		if response.status_code == 200:
			print("Screenshot saved successfully.")
		else:
			print("Failed to capture screenshot: " + response.text)