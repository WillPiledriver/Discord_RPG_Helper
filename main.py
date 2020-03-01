import tools
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

bot = commands.Bot(command_prefix='!')

customs = tools.rw_dict("custom_dice.json", "r", create=True)
stats = tools.rw_dict("stats.json", "r", create=True)


class AddCommands(commands.Cog):
    def __init__(self, b, cmnds):
        self.bot = b
        self.cmnds = cmnds

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        msg = message.content.split(" ")[0].lower()

        if msg in self.cmnds.keys():
            await message.channel.send(self.cmnds[msg])

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        pass

    @commands.command(name="addcommand", help="Adds a command")
    async def add_command(self, ctx, name, *args):
        self.cmnds[name] = " ".join(args)
        tools.rw_dict("commands.json", "w+", self.cmnds)
        await ctx.send(f'{name} command added and saved!')

    @commands.command(name="commands", help="Lists silly commands.")
    async def list_commands(self, ctx):
        await ctx.send("```" + "\t".join(self.cmnds.keys()) + "```")

    @commands.command(name="delcommand", help="Removes a command")
    async def remove_command(self, ctx, name):
        del self.cmnds[name]
        tools.rw_dict("commands.json", "w+", self.cmnds)
        await ctx.send(f'{name} command deleted!')


def main():
    bot.add_cog(AddCommands(bot, tools.rw_dict("commands.json", "r", create=True)))
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


main()
