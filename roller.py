import asyncio
import configparser
import logging
import random
import re

import yaboli
from yaboli.utils import *


# Turn all debugging on
asyncio.get_event_loop().set_debug(True)
#logging.getLogger("asyncio").setLevel(logging.INFO)
#logging.getLogger("yaboli").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


ROLL = r"[!/]r(oll)?\s+(.*)"
THROW     = r"\s*([+-])?\s*(\d+)?d(\d+)"       # 1: sign, 2: amount (default 1), 3: sides
ADVANTAGE = r"\s*([+-])?\s*(\d+)?([ad])d(\d+)" # 1: sign, 2: amount (default 2), 3: a/d, 4: sides
NUMBER    = r"\s*([+-])?\s*(\d+)"              # 1: sign, 2: number

class Roller(yaboli.Bot):
	LONG_HELP = (
		"!roll <dice> <description> - roll dice\n"
		"/roll can be used instead of !roll. !r and /r also work.\n"
		"\n"
		"Dice throws, can be added/subtracted to each other:\n"
		"XdY - Throw X Y-sided dice. X defaults to 1.\n"
		"XadY - Throw X Y-sided dice with advantage. X defaults to 2.\n"
		"XddY - Throw X Y-sided dice with disadvantage. X defaults to 2.\n"
		"X - Constant number\n"
		"\n"
		"Example throws:\n"
		"!roll d20\n"
		"/roll ad20 + 5 damage\n"
		"!r 2d20-d10+10\n"
	)

	async def on_command_specific(self, room, message, command, nick, argstr):
		if similar(nick, room.session.nick) and not argstr:
			await self.botrulez_ping(room, message, command)
			await self.botrulez_help(room, message, command, text=self.LONG_HELP)
			await self.botrulez_uptime(room, message, command)
			await self.botrulez_kill(room, message, command)
			await self.botrulez_restart(room, message, command)

	async def on_command_general(self, room, message, command, argstr):
		if not argstr:
			await self.botrulez_ping(room, message, command)
			await self.botrulez_help(room, message, command, text="I roll dice for dnd")

	async def on_send(self, room, message):
		await super().on_send(room, message)
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
		resultstr = ("d" if dis else "a") + resultstr
		return result, resultstr

	@staticmethod
	def number(number):
		return number, str(number)

def main(configfile):
	config = configparser.ConfigParser(allow_no_value=True)
	config.read(configfile)

	nick = config.get("general", "nick")
	cookiefile = config.get("general", "cookiefile", fallback=None)
	bot = Roller(nick, cookiefile=cookiefile)

	for room, password in config.items("rooms"):
		if not password:
			password = None
		bot.join_room(room, password=password)

	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main("roller.conf")
