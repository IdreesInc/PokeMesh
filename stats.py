import json

class Stats:
	def __init__(self, path: str):
		self.path = path
		self.create_first_time()
		self.load()
	
	def load(self):
		with open(self.path, "r") as f:
			data = json.load(f)
			self.buttons_pressed = data.get("buttons_pressed", 0)
			self.bonks = data.get("bonks", 0)
			self.rounds = data.get("rounds", 0)
			self.visited_locations = data.get("visited_locations", {})
			self.user_stats = data.get("user_stats", {})

	def save(self):
		with open(self.path, "w") as f:
			json.dump({
				"buttons_pressed": self.buttons_pressed,
				"bonks": self.bonks,
				"rounds": self.rounds,
				"visited_locations": self.visited_locations,
				"user_stats": self.user_stats
			}, f, indent=4)

	def create_first_time(self):
		try:
			with open(self.path, "x") as f:
				json.dump({}, f, indent=4)
		except FileExistsError:
			pass

	def increment_buttons_pressed(self, count: int = 1):
		self.buttons_pressed += count

	def increment_bonks(self, count: int = 1):
		self.bonks += count

	def increment_rounds(self, count: int = 1):
		self.rounds += count

	def increment_visited_location(self, location: str):
		self.visited_locations[location] = self.visited_locations.get(location, 0) + 1

	def increment_user_action(self, user: str):
		if user not in self.user_stats:
			self.user_stats[user] = {
			}
		self.user_stats[user]["actions"] = self.user_stats[user].get("actions", 0) + 1
