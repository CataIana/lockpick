from discord import Intents, TextChannel, PermissionOverwrite
from discord.errors import Forbidden, HTTPException
from discord.ext import commands
from traceback import format_exception
import logging
import sys

TOKEN = ""
access_roles = { #Both must be integers, NOT strings
    "GUILD_ID": "ROLE_ID"
}

class UwU(commands.Bot):
    def __init__(self, access_role):
        intents = Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True
        super().__init__(command_prefix="-", case_insensitive=True, intents=intents, help_command=None)
        self.access_role = access_role
        self.add_cog(CommandsCog(self))
        self.log_level = logging.INFO
        log_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

        self.log = logging.getLogger("lockpick")
        self.log.setLevel(self.log_level)
        handler = logging.StreamHandler(sys.stdout)                             
        handler.setLevel(self.log_level)                                        
        handler.setFormatter(log_format)                                        
        self.log.addHandler(handler)      
        #handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        #handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        #self.log.addHandler(handler)

    async def on_ready(self):
        self.log.info("Logged in as")
        self.log.info(self.user.name)
        self.log.info(self.user.id)
        self.log.info("------")

    async def on_command_error(self, ctx, exception):
        if isinstance(exception, commands.BotMissingPermissions):
            await ctx.send(content=exception)
            return
        if isinstance(exception, commands.ChannelNotFound):
            await ctx.send(content="Unable to locate channel")
            return
        ignored = (commands.CommandNotFound, commands.MissingRequiredArgument, commands.CheckFailure, commands.BadArgument)
        if isinstance(exception, ignored): return
        
        exception = getattr(exception, 'original', exception)

        await ctx.send(content="There was an error executing this command.")

        exc = ''.join(format_exception(type(exception), exception, exception.__traceback__))
        self.log.error(f"Ignoring exception in command {ctx.command}:\n{exc}")

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_permrole():
        async def predicate(ctx):
            return ctx.bot.access_role.get(ctx.guild.id, None) in [role.id for role in ctx.author.roles]
        return commands.check(predicate)

    @commands.command()
    @has_permrole()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lock(self, ctx, c: TextChannel = None):
        c = c or ctx.channel
        try:
            overwrite = c.overwrites[ctx.guild.default_role]
        except KeyError:
            overwrite = PermissionOverwrite()
        overwrite.send_messages = False
        overwrite.add_reactions = False
        await c.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.message.add_reaction("✅")
        self.bot.log.info(f"Locked #{c.name}")

    @commands.command()
    @has_permrole()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def unlock(self, ctx, c: TextChannel = None):
        c = c or ctx.channel
        try:
            overwrite = c.overwrites[ctx.guild.default_role]
        except KeyError:
            overwrite = PermissionOverwrite()
        overwrite.send_messages = None
        overwrite.add_reactions = None
        overwrite.speak = None
        await c.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.message.add_reaction("✅")
        self.bot.log.info(f"Unlocked #{c.name}")

    @commands.command(aliases=["nuke"])
    @has_permrole()
    @commands.bot_has_guild_permissions(ban_members=True)
    async def massBan(self, ctx, phrase: str):
        async for message in ctx.channel.history(limit=500):
            if phrase.lower() in message.content.lower() and message.author != ctx.author:
                self.bot.log.info(f"Banning user {message.author}")
                try:
                    await ctx.guild.ban(message.author, reason=f"{ctx.author}: Mass banned for phrase {phrase}", delete_message_days=1)
                except Forbidden:
                    pass
                except HTTPException:
                    pass
        await ctx.message.add_reaction("✅")
        self.bot.log.info(f'Finished massban on phrase "{phrase}"')

    

client = UwU(access_roles)
client.run(TOKEN)
