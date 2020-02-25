import tools
import json
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to discord!')


try:
    with open("custom_dice.json", "r") as file:
        customs = json.load(file)
except FileNotFoundError:
    with open("custom_dice.json", "w+") as file:
        file.write("{}")
        print("File created")
    customs = dict()

try:
    with open("stats.json", "r") as file:
        stats = json.load(file)
except FileNotFoundError:
    with open("stats.json", "w+") as file:
        file.write("{}")
        print("File created")
    stats = dict()

def main():
    bot.run(token)


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
    await ctx.send("{} set.".format(name))


@bot.command(name='lee', help="It's just a meme.")
async def lee(ctx):
    await ctx.send("Red is tens")


@bot.command(name='aaron', help="It's just a meme.")
async def aaron(ctx):
    await ctx.send("It's just a skin disease")


@bot.command(name="set", help="Set arbitrary player stats.")
async def set_stat(ctx, name, stat, number):
    if name.lower() not in stats:
        stats[name.lower()] = dict()
    stats[name.lower()][stat.lower()] = int(number)
    with open("stats.json", "w+") as stats_file:
        json.dump(stats, stats_file)
    await ctx.send(f'{name}\'s {stat} set to {number}')


@bot.command(name="get", help="Gets arbitrary player stat.")
async def get_stat(ctx, name, stat):
    await ctx.send(f'{name}\'s {stat} is {stats[name.lower()][stat.lower()]}.')


main()
