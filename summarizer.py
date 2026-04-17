import base64
import requests

class Summarizer:
	def __init__(self, secrets: dict, settings: dict):
		self.server = secrets["server"]
		self.server_token = secrets["server_token"]
		self.model = secrets["model"]
		self.prompt = settings["prompt"]

	def summarize(self, path: str, *extra_paths: str) -> str:
		return self.request(self.prompt, path, *extra_paths)

	def request(self, message: str, *image_paths: str) -> str:
		content: list = [
			{
				"type": "text",
				"text": message
			}
		]
		for image_path in image_paths:
			with open(image_path, "rb") as f:
				encoded = base64.b64encode(f.read()).decode("utf-8")
				content.append({
					"type": "image_url",
					"image_url": {
						"url": "data:image/png;base64," + encoded
					}
				})

		response = requests.post(
			"http://" + self.server + "/v1/chat/completions",
			headers={
				"Authorization": f"Bearer {self.server_token}"
			},
			json={
				"model": self.model,
				"messages": [
					{
						"role": "user",
						"content": content
					}
				]
			}
		)
		return response.json()["choices"][0]["message"]["content"]