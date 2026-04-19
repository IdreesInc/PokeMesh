import os
import json
import time
import base64
from summarizer import Summarizer
from preprocessor import preprocess

SECRETS: dict = json.load(open("secrets.json"))
SETTINGS: dict = json.load(open("settings.json"))

TEST_FOLDER = "tests"
IMAGE_FOLDER = "images"
TMP_FOLDER = "tmp"
OUTPUT_FOLDER = "outputs"

def main():
	print("Testing...")
	summaries: list[list[str]] = []
	summarizer = Summarizer(SECRETS, SETTINGS)
	tmp_path = os.path.join(TEST_FOLDER, TMP_FOLDER)
	os.makedirs(tmp_path, exist_ok=True)
	directory = os.fsencode(os.path.join(TEST_FOLDER, IMAGE_FOLDER))
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith(".png"): 
			print("Processing " + filename)
			src_path = os.path.join(TEST_FOLDER, IMAGE_FOLDER, filename)
			grid_path = os.path.join(tmp_path, filename)
			preprocess(src_path, grid_path, 16)
			t_start = time.time()
			summary = summarizer.summarize(grid_path)
			elapsed = time.time() - t_start
			with open(src_path, "rb") as img_f:
				data_url = "data:image/png;base64," + base64.b64encode(img_f.read()).decode()
			elapsed_str = f"{elapsed:.1f}s"
			print(f"Summary ({elapsed_str}): " + summary)
			summaries.append([filename, summary, data_url, elapsed_str])
	output_name = "test_output_" + str(int(time.time()))
	output_path = os.path.join(TEST_FOLDER, OUTPUT_FOLDER, output_name + ".md")
	print("Saving output to " + output_path)
	with open(output_path, "w") as f:
		f.write("# Test Output\n\n")
		f.write("Model: " + SETTINGS["model"] + "\n\n")
		f.write("```\n" + "\n".join(SETTINGS["prompt"]) + "\n```\n\n")
		f.write("## Tests\n\n")
		for summary in summaries:
			f.write("### " + summary[0] + "\n\n")
			f.write("![](" + summary[2] + ")\n\n")
			f.write(summary[1] + "\n\n")
			f.write("*" + summary[3] + "*\n\n")
	print("Testing complete!")

if __name__ == "__main__":
	main()