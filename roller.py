import asyncio
import random

import yaboli
from yaboli.utils import *

# List of rooms kept in separate file, which is .gitignore'd
import join_rooms


ROLL = r"[!/]roll (\d+)d(\d+)\s*(\+\s*(\d+))?"

class Roller(yaboli.Bot):
	async def send(self, room, message):
		long_help = (
			"!roll 2d4 - roll 2 4-sided dice\n"
			"!roll 2d4+5 - roll 2 4-sided dice with a bonus of 5\n"
			"/roll can be used instead of !roll.\n"
		)
		await self.botrulez_ping_general(room, message)
		await self.botrulez_ping_specific(room, message)
		await self.botrulez_help_general(room, message, help_text="I roll dice")
		await self.botrulez_help_specific(room, message, help_text=long_help)
		await self.botrulez_uptime(room, message)
		await self.botrulez_kill(room, message)
		await self.botrulez_restart(room, message)

		await self.trigger_roll(room, message)

	forward = send

	@yaboli.trigger(ROLL)
	async def trigger_roll(self, room, message, match):
		amount = int(match.group(1))
		sides = int(match.group(2))
		bonus = match.group(4)
		if bonus:
			bonus = int(bonus)

		results = [random.randint(1, sides) for roll in range(amount)]
		result = sum(results)
		resultstr = ", ".join(str(r) for r in results)

		if bonus is not None:
			text = f"{result + bonus}: {resultstr} + {bonus}"
		else:
			text = f"{result}: {resultstr}"

		await room.send(text, message.mid)

def main():
	bot = Roller("Roller", "roller.cookie")
	join_rooms.join_rooms(bot)
	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main()
