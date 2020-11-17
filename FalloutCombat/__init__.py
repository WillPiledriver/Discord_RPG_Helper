from discord.ext import commands
import discord
import asyncio
import datetime
from pprint import pprint
import math
import csv
import os
import re
import random as rand
from operator import itemgetter

OPTIONS_COMBAT_MAIN_MENU = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}


def csv_to_dict(relative_path, name):
    c = csv.DictReader(open(os.path.dirname(os.path.realpath(__file__)) + relative_path))
    return {row[name]: {x: row[x] for x in row if not x == name} for row in c}


class FalloutCombat(commands.Cog):
    def __init__(self, bot, game_name):

        self.attributes = "SPECIAL"

        self.skills = {"SG": {"eq": "5+4*{A}"},
                       "BG": {"eq": "2*{A}"},
                       "EW": {"eq": "2*{A}"},
                       "U": {"eq": "30+2*({A}+{S})"},
                       "M": {"eq": "20+2*({A}+{S})"},
                       "TH": {"eq": "4*{A}"},
                       "FA": {"eq": "2*({P}+{I})"},
                       "D": {"eq": "5+{P}+{I}"},
                       "SN": {"eq": "5+3*{A}"},
                       "LP": {"eq": "10+{P}+{A}"},
                       "ST": {"eq": "3*{A}"},
                       "TR": {"eq": "{P}+{A}"},
                       "SC": {"eq": "4*{I}"},
                       "R": {"eq": "3*{I}"},
                       "PI": {"eq": "2*({A}+{P})"},
                       "SP": {"eq": "5*{C}"},
                       "SU": {"eq": "2*({E}+{I})"},
                       }
        self.secondary = {"SQ": {"eq": "2*{P}"},
                          "AP": {"eq": "({A}/2)+5"},
                          "MD": {"eq": "{S}-5"},
                          "CRIT": {"eq": "{L}"}
                          }
        self.game_name = game_name
        self.bot = bot
        self.players = csv_to_dict(f"\\data\\{game_name}\\players.csv", "NAME")
        self.armors = csv_to_dict(f"\\data\\{game_name}\\armors.csv", "NAME")
        self.weapons = csv_to_dict(f"\\data\\{game_name}\\weapons.csv", "NAME")
        self.enemies = csv_to_dict(f"\\data\\{game_name}\\enemies.csv", "NAME")
        self.session = dict()
        self.approved_ids = [158862959534276608]
        self.temp_calc = None
        self.br = False
        self.clean_tables()
        print("Tables loaded.")

    def clean_tables(self):
        tables = [self.weapons, self.enemies, self.armors, self.players]
        for t in tables:
            for k, d in t.items():
                for kk, dd in d.items():
                    if dd.isnumeric():
                        t[k][kk] = int(t[k][kk])

    def generate_enemy(self, name, weapon=None, armor=None):
        enemy = dict(self.enemies[name])
        enemy["NAME"] = name
        randnum_match = re.compile("^[0-9]+-[0-9]+$")
        num_match = re.compile("^[0-9]+$")

        for key, value in enemy.items():
            if isinstance(value, (str,)) is False:
                continue
            if re.match(num_match, value):
                # Any integer
                enemy[key] = int(value)
            elif re.match(randnum_match, value):
                # Random number range
                splt = value.split("-")
                r = rand.randint(int(splt[0]), int(splt[1]))
                enemy[key] = r
            if value.count(",") > 0:
                # random list of strings
                enemy[key] = value.split(",")

        if weapon is None:
            if isinstance(enemy["WEAPON"], (list,)):
                # Random weapon
                enemy["WEAPON"] = enemy["WEAPON"][rand.randint(0, len(enemy["WEAPON"]) - 1)]
        else:
            enemy["WEAPON"] = weapon
        if armor is None:
            if isinstance(enemy["ARMOR"], (list,)):
                # Random armor
                enemy["ARMOR"] = enemy["ARMOR"][rand.randint(0, len(enemy["ARMOR"]) - 1)]
        else:
            enemy["ARMOR"] = armor

        if "BONUS" in enemy:
            # Parse and restructure bonuses
            if isinstance(enemy["BONUS"], (list,)):
                bns = {}
                for b in enemy["BONUS"]:
                    splt = b.split(" ")
                    if re.match(randnum_match, splt[1]):
                        splt2 = splt[1].split("-")
                        bns[splt[0]] = rand.randint(int(splt2[0]), int(splt2[1]))
                    else:
                        bns[splt[0]] = int(splt[1])
                enemy["BONUS"] = bns
            else:
                splt = enemy["BONUS"].split(" ")
                if re.match(randnum_match, splt[1]):
                    splt2 = splt[1].split("-")
                    r = rand.randint(int(splt2[0]), int(splt2[1]))
                else:
                    r = int(splt[1])
                enemy["BONUS"] = {splt[0]: r}
        enemy = self.populate(enemy)
        return enemy

    def populate(self, enemy):
        result = dict()
        result["skills"] = {key: dict(self.skills[key]) for key in self.skills}
        result["secondary"] = {key: dict(self.secondary[key]) for key in self.secondary}
        result["weapon"] = enemy["WEAPON"]
        result["armor"] = enemy["ARMOR"]
        result["bonus"] = enemy["BONUS"]

        attributes = {key.upper(): {"val": enemy[key]} for key in self.attributes
                      if key.upper() in enemy}

        result["attributes"] = attributes

        for skill in self.skills.keys():
            result["skills"][skill]["val"] = self.calc_base(attributes, self.skills[skill]["eq"])

        for secondary in self.secondary.keys():
            if secondary in enemy:
                result["secondary"][secondary]["val"] = enemy[secondary]
            else:
                result["secondary"][secondary]["val"] = self.calc_base(attributes, self.secondary[secondary]["eq"])
            if secondary == "AP" and result["secondary"][secondary]["val"] < 5:
                result["secondary"]["AP"]["val"] = 5
            if secondary == "MD" and result["secondary"][secondary]["val"] < 0:
                result["secondary"][secondary]["val"] = 0

        for key, value in result["bonus"].items():
            if key in result["skills"]:
                result["skills"][key]["val"] += value
            elif key in self.secondary:
                result["secondary"][key]["val"] += value
            else:
                print("bonus {} does nothing".format(key))
        result["bonus"] = dict()
        return result

    def calc_base(self, attributes, eq):
        """
        Calculates a given equation by replacing strings with variables.
        :param attributes: Dict of attributes with "var" keys.
        :param eq: Equation to perform.
        :return: Solution of the equation.
        """

        attributes = {key: attributes[key]["val"] for key in attributes.keys()}
        for key in attributes:
            eq = eq.replace("{"+key+"}", str(attributes[key]))
        exec("self.temp_calc=" + eq)
        return self.temp_calc

    @commands.command(name="reload", help="Reloads the CSV files into memory.")
    async def load_tables(self, ctx):
        self.players = csv_to_dict(f"\\data\\{self.game_name}\\players.csv", "NAME")
        self.armors = csv_to_dict(f"\\data\\{self.game_name}\\armors.csv", "NAME")
        self.weapons = csv_to_dict(f"\\data\\{self.game_name}\\weapons.csv", "NAME")
        self.enemies = csv_to_dict(f"\\data\\{self.game_name}\\enemies.csv", "NAME")
        await ctx.send("CSV files loaded successfully.")

    async def add_mobs(self, ctx):
        embed = discord.Embed(
            title="Please enter mobs delimited by commas. You can multiply the mobs with ~",
            description="**EXAMPLE:** molerat~2,scumbag~3",
            colour=ctx.author.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Combat")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        msg = await ctx.send(embed=embed)

        def is_correct(m):
            split_content = m.content.split(",")
            parsed_content = [p.split("~") for p in split_content]
            split_content = [((p[0]+",")*int(p[1])).rstrip(",") for p in parsed_content if len(p) == 2]
            for p in parsed_content:
                if len(p) == 1:
                    split_content.append(p[0])
            parsed_content = ",".join(split_content).split(",")
            result = all([m.author.id in self.approved_ids] + [(p in self.enemies) for p in parsed_content])
            self.parsed = parsed_content
            if not result:
                print("error")
            else:
                return True

        self.parsed = []
        answer = await self.bot.wait_for('message', check=is_correct)
        if answer:
            await msg.delete()

            async def generate_mobs(ctx):
                for name in self.parsed:
                    mob = self.generate_enemy(name)
                    mob["NAME"] = name
                    if "enemies" in self.session:
                        self.session["enemies"].append(mob)
                    else:
                        self.session["enemies"] = list()
                        self.session["enemies"].append(mob)

            await generate_mobs(ctx)

    async def add_players(self, ctx):
        t = [k for k, d in self.players.items()] + ["ALL", "ACCEPT"]
        while not self.br:
            embed = discord.Embed(
                title="Type in your answer.",
                description="\n".join([f"**{n+1}:** {t[n]}" for n in range(len(t))]),
                colour=ctx.author.colour,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(name="Combat")
            embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            msg = await ctx.send(embed=embed)

            def is_correct(m):
                cnt = m.content
                if cnt.isnumeric():
                    n = int(cnt)-1
                    if n < len(t) - 2:
                        if "players" not in self.session:
                            self.session["players"] = dict()
                        self.session["players"][t[n]] = self.players[t[n]]
                        del t[n]
                        return True
                    elif n < len(t) + 2:
                        if "players" not in self.session:
                            self.session["players"] = dict()
                        if t[n] == "ALL":
                            while len(t) > 2:
                                p = t.pop(0)
                                self.session["players"][p] = self.players[p]
                            self.br = True
                        elif t[n] == "ACCEPT":
                            self.br = True
                        return True

            answer = await self.bot.wait_for('message', check=is_correct)
            if answer:
                await msg.delete()

    async def reroll_mobs(self, ctx):
        if "enemies" in self.session:
            temp_enemies = list()
            for m in self.session["enemies"]:
                mob = self.generate_enemy(m["NAME"])
                mob["NAME"] = m["NAME"]
                temp_enemies.append(mob)
            self.session["enemies"] = temp_enemies
        await ctx.send("**ENEMIES REROLLED**")



    @commands.command(name="combat", help="Starts interactive combat embed.")
    async def combat(self, ctx):
        def _check(r, u):
            return (
                r.emoji in OPTIONS_COMBAT_MAIN_MENU.keys()
                and u == ctx.author
            )
        embed = discord.Embed(
            title="Combat Main Menu",
            description=f"**1.** Add mob\n**2.** Add player\n**3.** Reroll baddies\n**4.** Skirmish\n**5.** Quit",
            colour=ctx.author.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Combat")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        self.br = False
        while not self.br:

            msg = await ctx.send(embed=embed)
            for emoji in list(OPTIONS_COMBAT_MAIN_MENU.keys())[:5]:
                await msg.add_reaction(emoji)

            reaction, user = await self.bot.wait_for("reaction_add", check=_check)
            if user.id in self.approved_ids:
                await msg.delete()
                answer = OPTIONS_COMBAT_MAIN_MENU[reaction.emoji]
                if answer == 4:
                    self.br = True
                    continue
                do = [self.add_mobs, self.add_players, self.reroll_mobs]
                await do[answer](ctx)
                self.br = False