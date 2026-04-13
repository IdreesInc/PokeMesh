from pyboy import PyBoy

def main():
	print("Hello, World!")
	pyboy = PyBoy("resources/yellow.gb")
	while pyboy.tick():
		pass
	pyboy.stop()


if __name__ == "__main__":
	main()
