import base64
import requests

class Summarizer:
	def __init__(self, secrets: dict, settings: dict):
		self.server = secrets["server"]
		self.server_token = secrets["server_token"]
		self.model = secrets["model"]
		self.prompt = settings["prompt"]

	def summarize(self, path: str) -> str:
		return self.request(self.prompt, path)

	def request(self, message: str, image_path: str | None) -> str:
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