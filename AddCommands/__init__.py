from discord.ext import commands
import tools

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

    @commands.command(name="addcmd", help="Adds a command.")
    async def add_command(self, ctx, name, *args):
        self.cmnds[name] = " ".join(args)
        tools.rw_dict("commands.json", "w+", self.cmnds)
        await ctx.send(f'{name} command added and saved!')

    @commands.command(name="cmds", help="Lists silly commands.")
    async def list_commands(self, ctx):
        await ctx.send("```" + "\t".join(self.cmnds.keys()) + "```")

    @commands.command(name="delcmd", help="Removes a command.")
    async def remove_command(self, ctx, name):
        del self.cmnds[name]
        tools.rw_dict("commands.json", "w+", self.cmnds)
        await ctx.send(f'{name} command deleted!')