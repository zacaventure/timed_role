import datetime
import discord
import os
import pytz
from discord.ext.commands.errors import MissingPermissions
from dotenv import load_dotenv
from RoleTimeOutChecker import RoleTimeOutChecker
from discord.utils import get
from data import Data
from data_structure.GlobalTimeRole import GlobalTimedRole
from data_structure.TimedRole import TimedRole
from data_structure.Server import Server
import logging
from discord.ext.commands import has_permissions


# load .env variables
load_dotenv()

#logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")
logger.setLevel(logging.ERROR)
file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "timed_bot.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)
data = Data()
timeChecker = RoleTimeOutChecker(data, bot, logger)

guildIds = [833210288681517126] # test discord server
guildIds = None # force global commands

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    

def canTheBotHandleTheRole(ctx, role: discord.Role) -> bool:
    myBot: discord.Member = ctx.guild.get_member(bot.user.id)
    if myBot.top_role.position > role.position:
        return True
    return False

@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Show all the individual and global timed role of your server", default_permission=True)
async def show_timed_role_of_server(ctx):
    server = data.getServer(ctx.guild.id)
    embed = discord.Embed()
    
    value=""
    i = 1
    server.timedRoleOfServer = {k: v for k, v in sorted(server.timedRoleOfServer.items(), key=lambda item: item[1])} # Sort with expiration days
    for roleId, expirationDays in server.timedRoleOfServer.items():
        role_get = get(ctx.guild.roles, id=roleId)
        if role_get is not None:
            value += "{}) {} with {} days expiration\n".format(i, role_get.mention, expirationDays)
            i += 1
    if value == "":
        value = "No timed role for your server" 
    embed = discord.Embed(title="Timed role of your server", description=value)
    
    value=""
    i = 1
    server.globalTimeRoles.sort()
    for timeRole in server.globalTimeRoles:
        role_get = get(ctx.guild.roles, id=timeRole.roleId)
        if role_get is not None:
            value += "{}) {} expire on {} \n".format(i, role_get.mention, timeRole.printEndDate())
            i += 1
    if value == "":
        value = "No global timed role for your server" 
    embed2 = discord.Embed(title="Global timed role of your server", description=value)
    embed2.set_footer(text="Note: Global roles expire for everyone in the server at the same time !")
    await ctx.respond(embed=embed)
    await ctx.respond(embed=embed2)
    
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Show all the individual and global timed role of a member")
async def show_timed_role_of_member(ctx, member: discord.Member):
    server: Server = data.getServer(ctx.guild.id)
    embed = discord.Embed()
    
    value=""
    i = 1
    memberData = data.getMember(ctx.guild.id, member.id)
    memberData.timedRole.sort()
    for timeRole in memberData.timedRole:
        role_get = get(ctx.guild.roles, id=timeRole.roleId)
        if role_get is not None:
            value += "{}) {} with {} days left\n".format(i, role_get.mention, timeRole.getHowManyDayRemaining())
            i += 1
    if value == "":
        value = "No timed role for {}".format(member.name) 
    embed = discord.Embed(title="Timed role of {}".format(member.name), description=value)
    
    value=""
    i = 1
    server.globalTimeRoles.sort()
    for timeRole in server.globalTimeRoles:
        role_get = get(ctx.guild.roles, id=timeRole.roleId)
        if role_get in member.roles and role_get is not None:
            value += "{}) {} that expire for everyone on {} \n".format(i, role_get.mention, timeRole.printEndDate())
        i += 1
    if value == "":
        value = "No global timed role for {}".format(member.name) 
    embed2 = discord.Embed(title="Global timed role of {}".format(member.name), description=value)
    await ctx.respond(embed=embed)
    await ctx.respond(embed=embed2)
    
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Show all the user of a timed role. Show the members who have the role, without having a timed role")
async def show_timed_role_users(ctx, role: discord.Role):
    server = data.getServer(ctx.guild.id)
    guild = bot.get_guild(server.serverId)

    isTimedRoleGlobal=False
    positionGlobalTimedRole=0
    for globalTimedRole in server.globalTimeRoles:
        if globalTimedRole.roleId == role.id:
            isTimedRoleGlobal=True
            break
        positionGlobalTimedRole += 1
        
    description = ""
    memberDays = {}
    memberNoTimedRole = []
    for member in server.members:
        for timeRole in member.timedRole:
            if timeRole.roleId == role.id:
                memberDays[member.memberId] = timeRole.getHowManyDayRemaining()
                break
            
    guild : discord.Guild = bot.get_guild(server.serverId)
    for memberDiscord in guild.members:
        if role in memberDiscord.roles:
            if isTimedRoleGlobal:
                globalTimedRole = server.globalTimeRoles[positionGlobalTimedRole].getRemainingDays(server.timezone)
                if memberDiscord.id not in memberDays or globalTimedRole < memberDays[memberDiscord.id]:
                    memberDays[memberDiscord.id] = globalTimedRole
                    
            elif not isTimedRoleGlobal and memberDiscord.id not in memberDays:
                memberNoTimedRole.append(memberDiscord)
                
    memberDays = {k: v for k, v in sorted(memberDays.items(), key=lambda item: item[1])} # Sort with expiration days 
    for memberId, numberDays in memberDays.items():
        discord_member = guild.get_member(memberId)
        description += "{} with {} days left \n".format(discord_member.mention, numberDays)
    if description == "":
        description = "Nobody have this timed role"
    embed = discord.Embed(
        title="Has the timed role {}".format(role.name),
        description=description
    )
    
    description=""
    i = 1
    for discordMember in memberNoTimedRole:
        description += "{}) {} \n".format(i, discordMember.mention)
        i += 1
    embedNoTimedRole = discord.Embed(
        title="Has the role, but not a timed role for these members".format(role.name),
        description=description
    )
    await ctx.respond(embed=embed)
    if len(memberNoTimedRole) != 0:
        await ctx.respond(embed=embedNoTimedRole)

@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Add a new global time role with a expiration date.")    
@has_permissions(manage_roles=True)
async def add_global_timed_role(ctx, role: discord.Role, year: int, month: int, day: int, hour : int = 0, minute: int = 0):
    if not canTheBotHandleTheRole(ctx, role):
        await ctx.respond("That role {} is highter than the hightest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
        return
    server = data.getServer(ctx.guild.id)
    for globalTimeRole in server.globalTimeRoles:
        if globalTimeRole.roleId == role.id:
            globalTimeRole.endDate = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=server.timezone)
            await ctx.respond("The global role already exist... updating end date")
            return
        
    server.globalTimeRoles.append(GlobalTimedRole(role.id, datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=server.timezone)))
    data.saveData()
    await ctx.respond("The global role was added to the global timed role of the server")
    
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Remove a global role from the server")    
@has_permissions(manage_roles=True)
async def remove_global_timed_role(ctx, role: discord.Role):
    server = data.getServer(ctx.guild.id)
    i = 0
    found=False
    for globalTimeRole in server.globalTimeRoles:
        if globalTimeRole.roleId == role.id:
            found=True
            break
        i += 1
    if found:
        del server.globalTimeRoles[i]
        data.saveData()
        await ctx.respond("The global role was removed from the server !")
    else:
        await ctx.respond("This global time Role do not exist. run /show_timed_role_of_server to check what global timed role you have")
    
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Add a server timed role.Users getting that role will get a timed role")    
@has_permissions(manage_roles=True)
async def add_timed_role_to_server(ctx, role: discord.Role, number_of_days_given_to_member: int):
    if not canTheBotHandleTheRole(ctx, role):
        await ctx.respond("That role {} is highter than the hightest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
        return
    server = data.getServer(ctx.guild.id)
    server.timedRoleOfServer[role.id] = number_of_days_given_to_member
    data.saveData()
    await ctx.respond("The role was added to the timed role of the server with a {} days expiration".format(number_of_days_given_to_member))
   
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Remove a timed role of your server")     
@has_permissions(manage_roles=True)
async def remove_timed_role_from_server(ctx, role: discord.Role):
    server = data.getServer(ctx.guild.id)
    if role.id in server.timedRoleOfServer:
        del server.timedRoleOfServer[role.id]
        data.saveData()
        await ctx.respond("The role was removed !")
    else:
        await ctx.respond("The role is not a timed role of the server !")
     
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Manually add a timed role to a user")            
@has_permissions(manage_roles=True)
async def add_timed_role_to_user(ctx, member: discord.Member, role: discord.Role, number_of_days_to_keep_role: int):
    if not canTheBotHandleTheRole(ctx, role):
        await ctx.respond("That role {} is highter than the hightest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
        return
    memberData = data.getMember(member.guild.id, member.id)
    roleIn = False
    for timeRole in memberData.timedRole:
        if timeRole.roleId == role.id:
            roleIn = True
            break
        
    if not roleIn:
        memberData.timedRole.append(TimedRole(role.id, number_of_days_to_keep_role))
        data.saveData()
    await member.add_roles(role)
    await ctx.respond("Custom role delivered !")
    
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Remove a timed role from a user (not global tr)")      
@has_permissions(manage_roles=True)
async def remove_timed_role_from_user(ctx, member: discord.Member, role: discord.Role):
    memberData = data.getMember(member.guild.id, member.id)
    i = 0
    isIn = False
    for timeRole in memberData.timedRole:
        if timeRole.roleId == role.id:
            isIn = True
            break
        i += 1
    if isIn:
        del memberData.timedRole[i]
        data.saveData()
    await member.remove_roles(role)
    await ctx.respond("Custom role remove !")
      
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Show help window")
async def help(ctx):
    embed = discord.Embed()
    embed.add_field(name="Global roles (need manage_role)", value="Add a new global timed role for the server \n*/add_global_timed_role \<role\> \<year\> \<month\> \<day\> \[hour=0\] \[minute=0\]*\n\nRemove a global timed role for the server\n*/remove_global_timed_role \<role\>*", inline=True)
    embed.add_field(name="Individual Roles (need manage_role)", value="Add a new timed role for the server\n*/add_timed_role_to_server \<role\> \<numberOfDayUntilExpire\>*\n\nRemove a timed role for the server\n*/remove_timed_role_from_server \<role\>*\n\nManually add a timed role to a member\n*/add_timed_role_to_user \<member\> \<role\> \<numberOfDayUntilExpire\>*\n\nManually remove a timed role to a member\n*/remove_timed_role_from_user \<member\> \<role\>*", inline=False)
    embed.add_field(name="Get information", value="Show all timed role of the server\n*/show_timed_role_of_server*\n\nShow all member of a timed role\n*/show_timed_role_of_member <role>*\n\nGet all timed role of a user\n*/show_timed_role_users <member>*", inline=True)
    embed.add_field(name="Timezones", value="Show the timezone of your server\n*/show_timezone*\n\nSet the timezone of your server\n*/set_timezone <timezone>* find the available timezone at https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568", inline=True)

    await ctx.respond(embed=embed)
    
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Update the timezone of the server")
@has_permissions(manage_roles=True)
async def set_timezone(ctx, timezone: str):
    if timezone not in pytz.all_timezones:
        await ctx.respond("Invalid timezone, check all available timezone here : {}".format("https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"))
    else:
        server = data.getServer(ctx.guild.id)
        server.timezone = pytz.timezone(timezone)
        data.saveData()
        await ctx.respond("The timezone for your server have been updated !")
        
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Show the timezone of the server")
async def show_timezone(ctx):
    server = data.getServer(ctx.guild.id)
    if server.timezone is None:
        await ctx.respond("You did not set a timezone yet ! use /set_timezone <timezone> to set one")
    else:
        await ctx.respond("The timezone for your server is {} and it is currently {} !".format(server.timezone, datetime.datetime.now(tz=server.timezone).strftime("%Y-%m-%d at %H:%M:%S")))

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
    
@add_global_timed_role.error
async def add_global_timed_role_error(ctx, error):
    await handleErrorGlobal(ctx, error)
    
@remove_global_timed_role.error
async def remove_global_timed_role_error(ctx, error):
    await handleErrorGlobal(ctx, error)
    
@add_timed_role_to_server.error
async def add_timed_role_to_server_error(ctx, error):
    await handleErrorGlobal(ctx, error)
    
@remove_timed_role_from_server.error
async def remove_timed_role_from_server_error(ctx, error):
    await handleErrorGlobal(ctx, error)
    
@add_timed_role_to_user.error
async def add_timed_role_to_user_error(ctx, error):
    await handleErrorGlobal(ctx, error)
        
@remove_timed_role_from_user.error
async def remove_timed_role_from_user_error(ctx, error):
    await handleErrorGlobal(ctx, error)
    
@set_timezone.error
async def set_timezone_error(ctx, error):
    await handleErrorGlobal(ctx, error)
    
async def handleErrorGlobal(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that! You need to have manage_role permission".format(ctx.author.name)
        await ctx.respond(text)
        
bot.run(os.getenv("TOKEN"))