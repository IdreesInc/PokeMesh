# PokeMesh: MeshCore Plays Pokémon

![License](https://img.shields.io/github/license/IdreesInc/PokeMesh)
[![Discord](https://img.shields.io/discord/1398471368403583120?logo=discord&logoColor=fff&label=discord&color=5865F2)](https://discord.gg/6yxE9prcNc)

PokeMesh is a collaborative game of Pokémon FireRed played over a decentralized network! The game view is processed and summarized, effectively turning the game into a text-based adventure over MeshCore. In the style of "Twitch Plays Pokémon", players submit inputs and the most requested inputs are ran every 30s to progress through the game!

*Note: PokeMesh is not affiliated with Nintendo, Game Freak, or the Pokémon Company. Pokémon and all related content are trademarks of Nintendo.*

## How to Play

PokeMesh is currently running in the San Francisco Bay Area mesh network. To play, connect to the #bot channel on MeshCore and submit inputs in the format `/poke [input] [times]` (e.g. `/poke up 2 right a 3` will press up twice, then right once, then a three times). You can also submit queries in the format `/poke [query]` (e.g. `/poke where`) to get information about the game! Type in `/poke help` to view all the available commands.

## How It Works

1. A user submits an input command like `/poke up 2 right a 3` in the configured MeshCore channel
2. The PokeMesh instance running on a server connected to a MeshCore companion node receives the command
3. Every 15 seconds, the queries are counted and the most popular input sequence is executed on a live game of Pokémon FireRed
4. After everything is executed, a screenshot of the game is taken
5. The screenshot is first processed by the "preprocessor"
6. The preprocessor output is sent to a local VLM along with a custom prompt to generate a summary of the current game state
7. The summary is posted back onto MeshCore and a new round starts

### Preprocessor

The preprocessor takes the original screenshot and makes it easier for the VLM to process. While this might not be necessary for more powerful models, it allows local models to better understand what they're seeing and significantly reduces mistakes. It also allows us to pre-identify important sprites like entrances and exits for better pathfinding.

The preprocessor first breaks down the screenshot into the individual tiles that make up the screen render. Certain tiles are identified and replaced with template tiles that are easier for the VLM to identify. For example, multiple kinds of doors will be replaced by a single "door" tile that is later described in the VLM prompt.

The preprocessor then stitches the tiles back together into the output image, along with a grid overlay allows the VLM to better understand the positions and possible movement options available to the player. A legend is drawn outside the screenshot on each axis to define positions as relational to the player at the origin.

Replaced tiles are stored and certain tiles are passed to the VLM as part of the prompt. This not only reduces mistakes in identifying those specific objects, but it has also been found to improve the identification of other tiles that weren't pre-identified as well.

## How to Run

1. Clone the repository and install the requirements with uv
2. Download a development build of the [mGBA emulator](hhttps://mgba.io/downloads.html)
   - A development build is required for running a Lua script on startup
   - You can use a normal build, but you will have to manually run the mGBA-http Lua script every time you start the emulator
3. Download the [mGBA-http](https://github.com/nikouu/mGBA-http) Lua script and executable
4. Place the mGBA executable, mGBA-http executable, Lua script, and your game rom in the `mgba` folder
5. Create a `secrets.json` file in the root directory following the format in `example_secrets.json`
6. Run the emulator with `start_emulator.sh` (make sure to update the ROM path in `start_emulator.sh` if you're not using the `secrets.json` method)
7. Run `main.py` to start the bot!

## Getting in Touch

If you'd like to get in touch, check out the [Discord](https://discord.gg/6yxE9prcNc) to suggest features, report bugs, and stay updated on development!

Also feel free to check out my other open-source projects like [Monocraft](https://github.com/IdreesInc/Monocraft), [PicoChat](https://github.com/IdreesInc/PicoChat), and more on [my website](https://idreesinc.com/)!

## Disclaimer

*This program uses a VLM (Vision Language Model) to process the game screenshots, but like all of my open-source projects, PokeMesh was not "vibe coded". While you are welcome to use whatever tools you prefer to contribute, please be sure to review all code by hand and do not blindly commit.*