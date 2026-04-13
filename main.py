import json
import requests
from pyboy import PyBoy

SETTINGS = json.load(open("settings.json"))
SERVER = SETTINGS["server"]
MODEL = SETTINGS["model"]


def main():
	print(request("Echo 'Hello, World!'"))
	# pyboy = PyBoy("resources/yellow.gb")
	# while pyboy.tick():
	# 	pass
	# pyboy.stop()

def request(message: str) -> str:
	response = requests.post(
		"http://" + SERVER + "/v1/chat/completions",
		json={
			"model": MODEL,
			"messages": [
				{
					"role": "user",
					"content": message
				}
			]
		}
	)
	return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
	main()
