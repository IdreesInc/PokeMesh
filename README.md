# MeshCore Plays Pokémon

![License](https://img.shields.io/github/license/IdreesInc/PokeMesh)
[![Discord](https://img.shields.io/discord/1398471368403583120?logo=discord&logoColor=fff&label=discord&color=5865F2)](https://discord.gg/6yxE9prcNc)

PokeMesh is a collaborative game of Pokémon FireRed played over a decentralized network! A local LLM reads and summarizes the screen, effectively turning the game into a text-based adventure over MeshCore. Players submit inputs and the most requested inputs are ran every 30s to progress through the game!

*Note: PokeMesh is not affiliated with Nintendo, Game Freak, or the Pokémon Company. Pokémon and all related content are trademarks of Nintendo.*

## How to Play

PokeMesh is currently running in the San Francisco Bay Area mesh network. To play, connect to the #bot channel on MeshCore and submit inputs in the format `/poke [input] [times]` (e.g. `/poke up 2 right a 3` will press up twice, then right once, then a three times). You can also submit queries in the format `/poke [query]` (e.g. `/poke where`) to get information about the game! Type in `/poke help` to view all the available commands.

## How to Run

1. Clone the repository and install the requirements with uv
2. Download and run the [mGBA emulator](https://github.com/mgba-emu/mgba) with a Pokémon FireRed ROM
3. Download and run the [mGBA-http](https://github.com/nikouu/mGBA-http) Lua script in the emulator and the executable containing the command server
4. Change the `secrets.json` file to point to your LLM provider and mGBA-http server
5. Run `main.py` to start the bot!

## Getting in Touch

If you'd like to get in touch, check out the [Discord](https://discord.gg/6yxE9prcNc) to suggest features, report bugs, and stay updated on development!

Also feel free to check out my other open-source projects like [Monocraft](https://github.com/IdreesInc/Monocraft), [PicoChat](https://github.com/IdreesInc/PicoChat), and more on [my website](https://idreesinc.com/)!
