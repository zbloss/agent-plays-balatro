# Warp Gameplan

I need your help building this agent fleet to play Balatro.

I have found the Balatro Wiki and built out some basic knowledge of the game, but feel free to add to it.

Here is the wikipedia article, browse it to get an understanding of the game: https://en.wikipedia.org/wiki/Balatro


## Agent Fleet

I need you to build an agent or a fleet of agents that can play Balatro.

The agents should be able to:

*   Observe the game state
*   Make decisions based on the game state
*   Take actions based on the decisions
*   Learn from the game to improve future performance using Memory
*   Adapt to different game situations
*   Identify what cards are in the hand
*   Identify what cards have already been played
*   Identify what cards are in the shop
*   Identify what jokers are in the shop
*   Identify what tarot cards are in the shop
*   Identify what spectral cards are in the shop
*   Identify what booster packs are in the shop
*   Identify what vouchers are in the shop
*   Identify what jokers I currently have
*   Calculate the value of different hands, including joker effects


## Technical requirements

* This should all be done in python.
* Use the autogen library to build the agents.
* Place python code within src/balatro_agent/
* Place any assets within assets/
* Use the balatro_agent/config/__init__.py file to store any configuration values

