import tools
import os
import random
from Cards import Cards
from dotenv import load_dotenv
from discord.ext import commands
from AddCommands import AddCommands
from FalloutCombat import FalloutCombat
from RadioBot import Music
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
load_dotenv()
bot = commands.Bot(command_prefix='!')

customs = tools.rw_dict("custom_dice.json", "r", create=True)
stats = tools.rw_dict("stats.json", "r", create=True)

deck = Cards()


def main():
    bot.add_cog(AddCommands(bot, tools.rw_dict("commands.json", "r", create=True)))
    bot.add_cog(Music(bot))
    bot.add_cog(FalloutCombat(bot, "FNT"))
    bot.run(os.getenv('DISCORD_TOKEN'))


@bot.command(name='roll', help='Rolls dice.')
async def roll(ctx, dice):
    if dice in customs:
        dice = customs[dice]

    dice_set = dice.split(";")
    output = "```"
    try:
        for d in range(len(dice_set)):
            dice = dice_set[d]
            output += "\n[{}]:\n".format(dice)
            dice_mult = dice.split("*")
            multi = 1
            if len(dice_mult) > 1:
                multi = int(dice_mult[1])
            dice = dice_mult[0]
            dice_split = dice.split("+")
            for i in range(multi):
                if len(dice_split) > 1:
                    result = tools.roll(dice_split[0], int(dice_split[1]))
                else:
                    result = tools.roll(dice)
                output += "\tRoll {}: {}\n".format(i+1, result)
        await ctx.send(output + "```")
    except Exception as e:
        print("Something went terribly wrong.")
        print(e)


@bot.command(name='setroll', help='Set a custom roll.')
async def set_roll(ctx, name, r):
    customs[name] = r
    tools.rw_dict("custom_dice.json", "w+", customs)
    await ctx.send("{} set.".format(name))


@bot.command(name='bugs', help='Bug loot table.')
async def bug_spawner(ctx, n=1):
    rarities = [("Legendary", .1), ("Uncommon", .3), ("Common", .6)]
    converted = []
    # Assumes rarities are in order from rare -> common
    for x in range(len(rarities)):
        mn = sum([rarities[i][1] for i in range(x)])
        mx = mn + rarities[x][1]
        converted.append((rarities[x][0], (mn, mx)))
    result = []
    fhack = "\n"
    for i in range(n):
        r = random.random()
        for rarity, (mn, mx) in converted:
            if mn <= r < mx:
                result.append(f'{rarity}: {r}')
    await ctx.send(f'```{fhack.join(result)}```')


@bot.command(name="set", help="Set arbitrary player stats.")
async def set_stat(ctx, name, stat, number):
    if name.lower() not in stats:
        stats[name.lower()] = dict()
    stats[name.lower()][stat.lower()] = number
    tools.rw_dict("stats.json", "w+", stats)
    await ctx.send(f'{name}\'s {stat} set to {number}')


@bot.command(name="get", help="Gets arbitrary player stat.")
async def get_stat(ctx, name, stat=None):
    if stat is None:
        result = f'```{name}\'s stats:\n'

        for k, d in stats[name.lower()].items():
            result += f'\t{k}: {d}\n'
        result += "```"

        await ctx.send(result)
        return
    await ctx.send(f'{name}\'s {stat} is {stats[name.lower()][stat.lower()]}.')


@bot.command(name="shuffle", help="Shuffle the deck.")
async def shuffle(ctx):
    deck.shuffle_deck()
    await ctx.send("Shuffled deck.")


@bot.command(name="draw", help="Draws x cards.")
async def draw(ctx, n=1):
    hand = deck.draw(n)
    result = list()
    for h in hand:
        result.append(f'{h[1]} of {h[0]}')
    result = "\n".join(result)
    await ctx.send(f'```{result}```')

main()
