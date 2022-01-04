import datetime
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from RoleTimeOutChecker import RoleTimeOutChecker
from discord.utils import get
from data import Data
from data_structure.GlobalTimeRole import GlobalTimedRole
from data_structure.TimedRole import TimedRole
from data_structure.Server import Server
import logging

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
bot = commands.Bot(command_prefix="%", intents = intents)
data = Data()
timeChecker = RoleTimeOutChecker(data, bot)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    
@bot.command(pass_context = True , aliases=["agtr"])
async def addGlobalTimeRole(ctx, role: discord.Role, year: int, month: int, day: int, hour : int = 0):
    server = data.getServer(ctx.guild.id)
    for globalTimeRole in server.globalTimeRoles:
        if globalTimeRole.roleId == role.id:
            globalTimeRole.endDate = datetime.datetime(year=year, month=month, day=day)
            await ctx.send("The global role already exist... updating end date")
            return
        
    server.globalTimeRoles.append(GlobalTimedRole(role.id, datetime.datetime(year=year, month=month, day=day, hour=hour)))
    data.saveData()
    await ctx.send("The global role was added to the global timed role of the server")
    
@bot.command(pass_context = True , aliases=["rgtr"])
async def removeGlobalTimeRole(ctx, role: discord.Role):
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
        await ctx.send("The global role was removed from the server !")
    else:
        await ctx.send("This global time Role do not exist. run $str to check what global timed role you have")
    
@bot.command(pass_context = True , aliases=["atr"])
async def addTimedRole(ctx, role: discord.Role, numberOfDay: int):
    server = data.getServer(ctx.guild.id)
    server.timedRoleOfServer[role.id] = numberOfDay
    data.saveData()
    await ctx.send("The role was added to the timed role of the server with a {} days expiration".format(numberOfDay))
    
@bot.command(pass_context = True , aliases=["rtr"])
async def removeTimedRole(ctx, role: discord.Role):
    server = data.getServer(ctx.guild.id)
    if role.id in server.timedRoleOfServer:
        del server.timedRoleOfServer[role.id]
        data.saveData()
        await ctx.send("The role was removed !")
      
@bot.command(pass_context = True , aliases=["str"])
async def showTimeRole(ctx):
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
    await ctx.send(embed=embed)
    
    value=""
    i = 1
    server.globalTimeRoles.sort()
    for timeRole in server.globalTimeRoles:
        role_get = get(ctx.guild.roles, id=timeRole.roleId)
        if role_get is not None:
            value += "{}) {} expire on {} \n".format(1, role_get.mention, timeRole.endDate)
            i += 1
    if value == "":
        value = "No global timed role for your server" 
    embed = discord.Embed(title="Global timed role of your server", description=value)
    embed.set_footer(text="Note: Global roles expire for everyone in the server at the same time !")
    await ctx.send(embed=embed)
    
@bot.command(pass_context = True , aliases=["tr"])
async def userTimeRole(ctx, member: discord.Member):
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
    await ctx.send(embed=embed)
    
    value=""
    i = 1
    server.globalTimeRoles.sort()
    for timeRole in server.globalTimeRoles:
        role_get = get(ctx.guild.roles, id=timeRole.roleId)
        if role_get in member.roles and role_get is not None:
            value += "{}) {} that expire for everyone on {} \n".format(i, role_get.mention, timeRole.endDate)
        i += 1
    if value == "":
        value = "No global timed role for {}".format(member.name) 
    embed = discord.Embed(title="Global timed role of {}".format(member.name), description=value)
    await ctx.send(embed=embed)
    
    
@bot.command(pass_context = True , aliases=["helpTimeRole", "htr"])
async def _showHelpTimeRole(ctx):
    embed = discord.Embed()
    embed.add_field(name="Global roles", value="Add a new global timed role for the server \n*%addGlobalTimeRole(agtr) \<role\> \<year\> \<month\> \<day\> \[hour=0\]*\n\nRemove a global timed role for the server\n*%removeGlobalTimeRole(rgtr) \<role\>*", inline=False)
    embed.add_field(name="Individual Roles", value="Add a new timed role for the server\n*%addTimeRole(atr) \<role\> \<numberOfDayUntilExpire\>*\n\nRemove a timed role for the server\n*%removeTimeRole(rtr) \<role\>*\n\nManually add a timed role to a member\n*%manualAddTimedRole(matr) \<member\> \<role\> \<numberOfDayUntilExpire\>*\n\nManually remove a timed role to a member\n*%manualRemoveTimedRole(mrtr) \<member\> \<role\>*", inline=True)
    embed.add_field(name="Get information", value="Show all timed role of the server\n*%showTimeRole(str)*\n\nShow all member of a timed role\n*%memberTimeRole(mtr) <role>*\n\nGet all timed role of a user\n*%tr <member>*")
    await ctx.send(embed=embed)
    
@bot.command(pass_context = True , aliases=["mtr"])
async def showMemberTimedRole(ctx, role: discord.Role):
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
                globalTimedRole = server.globalTimeRoles[positionGlobalTimedRole].getRemainingDays()
                if memberDiscord.id not in memberDays or globalTimedRole < memberDays[member.memberId]:
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
    if description == "":
        description = "Nobody have this timed role"
    embedNoTimedRole = discord.Embed(
        title="Has the role, but not a timed role for these members".format(role.name),
        description=description
    )
    await ctx.send(embed=embed)
    if len(memberNoTimedRole) != 0:
        await ctx.send(embed=embedNoTimedRole)
    
@bot.command(pass_context = True , aliases=["matr"])
async def manualAddTimedRole(ctx, memberDiscord: discord.Member, role: discord.Role, numberOfDay: int):
    member = data.getMember(memberDiscord.guild.id, memberDiscord.id)
    roleIn = False
    for timeRole in member.timedRole:
        if timeRole.roleId == role.id:
            roleIn = True
            break
        
    if not roleIn:
        member.timedRole.append(TimedRole(role.id, numberOfDay))
        data.saveData()
    await memberDiscord.add_roles(role)
    await ctx.send("Custom role delivered !")
    
@bot.command(pass_context = True , aliases=["mrtr"])
async def manualRemoveTimedRole(ctx, memberDiscord: discord.Member, role: discord.Role):
    member = data.getMember(memberDiscord.guild.id, memberDiscord.id)
    i = 0
    isIn = False
    for timeRole in member.timedRole:
        if timeRole.roleId == role.id:
            isIn = True
            break
        i += 1
    if isIn:
        del member.timedRole[i]
        data.saveData()
    await memberDiscord.remove_roles(role)
    await ctx.send("Custom role remove !")
    
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

bot.run(os.getenv('TOKEN'))