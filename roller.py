import asyncio
import logging
import random
import re

import yaboli
from yaboli.utils import *
from join_rooms import join_rooms # List of rooms kept in separate file, which is .gitignore'd

# Turn all debugging on
asyncio.get_event_loop().set_debug(True)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("yaboli").setLevel(logging.DEBUG)


ROLL = r"[!/]r(oll)?\s+(.*)"
THROW     = r"\s*([+-])?\s*(\d+)?d(\d+)"       # 1: sign, 2: amount (default 1), 3: sides
ADVANTAGE = r"\s*([+-])?\s*(\d+)?([ad])d(\d+)" # 1: sign, 2: amount (default 2), 3: a/d, 4: sides
NUMBER    = r"\s*([+-])?\s*(\d+)"              # 1: sign, 2: number

class Roller(yaboli.Bot):
	async def on_send(self, room, message):
		long_help = (
			"!roll 2d4 - roll 2 4-sided dice\n"
			"!roll 2d4+5 - roll 2 4-sided dice with a bonus of 5\n"
			"/roll can be used instead of !roll.\n"
		)
		await self.botrulez_ping_general(room, message)
		await self.botrulez_ping_specific(room, message)
		await self.botrulez_help_general(room, message, text="I roll dice")
		await self.botrulez_help_specific(room, message, text=long_help)
		await self.botrulez_uptime(room, message)
		await self.botrulez_kill(room, message)
		await self.botrulez_restart(room, message)

		await self.trigger_roll(room, message)

	@yaboli.trigger(ROLL)
	async def trigger_roll(self, room, message, match):
		result = 0
		resultstr = ""
		info = None

		rest = match.group(2)
		while True:
			mthrow,     mthrowrest     = self.match_and_split(THROW, rest)
			madvantage, madvantagerest = self.match_and_split(ADVANTAGE, rest)
			mnumber,    mnumberrest    = self.match_and_split(NUMBER, rest)
			if mthrow:
				sign = self.to_sign(mthrow.group(1))
				amount = self.to_amount(mthrow.group(2), default=1)
				sides = self.to_amount(mthrow.group(3))
				r, rstr = self.throw(amount, sides)
				rest = mthrowrest
			elif madvantage:
				sign = self.to_sign(madvantage.group(1))
				amount = self.to_amount(madvantage.group(2), default=2)
				dis = True if madvantage.group(3) == "d" else False
				sides = self.to_amount(madvantage.group(4))
				r, rstr = self.advantage(dis, amount, sides)
				rest = madvantagerest
			elif mnumber:
				sign = self.to_sign(mnumber.group(1))
				amount = self.to_amount(mnumber.group(2))
				r, rstr = self.number(amount)
				rest = mnumberrest
			elif rest.strip():
				if rest[0].isspace():
					info = rest.strip()
					break
				else:
					await room.send(f"Syntax error at {rest!r}", message.mid)
					return
			else:
				break

			result += sign * r
			if resultstr:
				resultstr += f" {'+' if sign == 1 else '-'} "
			elif sign == -1:
				resultstr += "-"
			resultstr += rstr

		if info:
			resultstr = f"{result}: {resultstr} {info}"
		else:
			resultstr = f"{result}: {resultstr}"
		await room.send(resultstr, message.mid)

	@staticmethod
	def match_and_split(regex, string):
		match = re.match(regex, string)
		if match:
			string = string[match.end():]
		return match, string

	@staticmethod
	def to_sign(string):
		if string == "-":
			return -1
		else:
			return 1

	@staticmethod
	def to_amount(string, default=0):
		if string is None:
			return default
		else:
			return int(string)

	@staticmethod
	def throw(amount, sides):
		results = [random.randint(1, sides) for _ in range(amount)]
		result = sum(results)
		resultstr = "(" + "+".join(str(r) for r in results) + ")"
		return result, resultstr

	@staticmethod
	def advantage(dis, amount, sides):
		results = [random.randint(1, sides) for _ in range(amount)]
		result = min(results) if dis else max(results)
		resultstr = "(" + ",".join(str(r) for r in results) + ")"
		resultstr = ("min" if dis else "max") + resultstr
		return result, resultstr

	@staticmethod
	def number(number):
		return number, str(number)

def main():
	bot = Roller("Roller", "roller.cookie")
	join_rooms(bot)
	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main()
