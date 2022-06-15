import discord
import os
from discord.ext.commands.errors import MissingPermissions
from MarkdownDiscord import Message
from RoleTimeOutChecker import RoleTimeOutChecker
from discord.utils import get
from cogs.AddCog import AddCog
from cogs.RemoveCog import RemoveCog
from cogs.ShowCog import ShowCog
from cogs.TimezoneCog import TimezoneCog
from data import Data
from data_structure.TimedRole import TimedRole
from data_structure.Server import Server
import logging
from constant import TOKEN, guildIds


#logging
logger = logging.getLogger("discord_commands")
logger.setLevel(logging.ERROR)
file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "commands.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

loggerStart = logging.getLogger("discord_start")
loggerStart.setLevel(logging.INFO)
file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "start.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
loggerStart.addHandler(handler)


intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)
data = Data()
timeChecker = RoleTimeOutChecker(data, bot)

bot.add_cog(TimezoneCog(bot, data))
bot.add_cog(ShowCog(bot, data))
bot.add_cog(RemoveCog(bot, data))
bot.add_cog(AddCog(bot, data))

@bot.event
async def on_guild_join(guild: discord.Guild):
    loggerStart.log(logging.INFO, "Bot just joined {}. The bot is not in {} guilds. Guilds: {}".format(guild.name, len(bot.guilds), bot.guilds))

@bot.event
async def on_guild_remove(guild: discord.Guild):
    loggerStart.log(logging.INFO, "Bot just left {}. The bot is not in {} guilds. Guilds: {}".format(guild.name, len(bot.guilds), bot.guilds))
    server = data.getServer(guild.id)
    data.servers.remove(server)
    data.saveData()

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    loggerStart.log(logging.INFO, "Bot in {} guilds. Guilds: {}".format(len(bot.guilds), bot.guilds))
    try:
        if checkForServerTheBotIsNoLongerIn():
            data.saveData()
        timeChecker.start()
    except Exception as error:
        loggerStart.log(logging.ERROR, "Error while starting up. Excepton {}".format(error))
    loggerStart.log(logging.INFO, "Setup finish")
    

def checkForServerTheBotIsNoLongerIn():
    serversToDelete = []
    for server in data.servers:
        isIn = False
        for guild in bot.guilds:
            if server.serverId == guild.id:
                isIn = True
                break
        if not isIn:
            serversToDelete.append(server)
            
    for serverToDelete in serversToDelete:
        data.servers.remove(serverToDelete)
    
    return len(serversToDelete) != 0
      
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Show help window")
async def help(ctx):
    await ctx.defer()
    embed = discord.Embed()
    embed.add_field(name="Global roles (need manage_role)", value="Add a new global timed role for the server \n*/add_global_timed_role \<role\> \<year\> \<month\> \<day\> \[hour=0\] \[minute=0\]*\n\nRemove a global timed role for the server\n*/remove_global_timed_role \<role\>*", inline=True)
    embed.add_field(name="Individual Roles (need manage_role)", value="Add a new timed role for the server\n*/add_timed_role_to_server \<role\> \<numberOfDayUntilExpire\>*\n\nRemove a timed role for the server\n*/remove_timed_role_from_server \<role\>*\n\nManually add a timed role to a member\n*/add_timed_role_to_user \<member\> \<role\> \<numberOfDayUntilExpire\>*\n\nManually remove a timed role to a member\n*/remove_timed_role_from_user \<member\> \<role\>*", inline=False)
    embed.add_field(name="Get information", value="Show all timed role of the server\n*/show_timed_role_of_server*\n\nShow all member of a timed role\n*/show_timed_role_of_member <role>*\n\nGet all timed role of a user\n*/show_timed_role_users <member>*", inline=True)
    embed.add_field(name="Timezones", value="Show the timezone of your server\n*/show_timezone*\n\nSet the timezone of your server(need manage_role)\n*/set_timezone <timezone>* find the available timezone at https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568", inline=True)

    await ctx.respond(embed=embed)
    
@bot.event
async def on_member_update(before, after):
    if len(before.roles) < len(after.roles):
        roleAdded = list(set(after.roles) - set(before.roles))[0]
        data.addTimedRole(after.guild.id, after.id, roleAdded.id)
    elif len(before.roles) > len(after.roles):
        roleRemove = list(set(before.roles) - set(after.roles))[0]
        member = data.getMember(after.guild.id, after.id)
        i = 0
        isIn = False
        for timeRole in member.timedRole:
            if timeRole.roleId == roleRemove.id:
                isIn = True
                break
            i += 1
        if isIn:
            del member.timedRole[i]
            data.saveData()
    
@bot.event
async def on_application_command_error(ctx, error: Exception):
    if isinstance(error, MissingPermissions):
        message = Message();
        message.addLine("Sorry {}, you do not have permissions to do that! You need to have manage_role permission".format(ctx.author.mention))
        embed = discord.Embed(title="Missing permissions", description=message.getString());
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(title="Unexpected error (this error will be log and look into)", description=error);
        await ctx.respond(embed=embed)
        logger.exception("On {} Exception: {}".format(ctx.guild, error))

        
bot.run(TOKEN)