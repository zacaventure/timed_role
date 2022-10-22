import asyncio
from datetime import datetime, timedelta
import discord
import os
from discord.ext.commands.errors import MissingPermissions
from BackupGenerator import BackupGenerator
from MarkdownDiscord import Message
from RoleTimeOutChecker import RoleTimeOutChecker
from cogs.AddCog import AddCog
from cogs.RemoveCog import RemoveCog
from cogs.ShowCog import ShowCog
from cogs.TimezoneCog import TimezoneCog
from discord.ext.commands import Bot
import logging
import database.database as database
from constant import LOCAL_TIME_ZONE, TOKEN, LOG_DIR_PATH, guildIds

logging.Formatter.converter = lambda *args: datetime.now(tz=LOCAL_TIME_ZONE).timetuple()

if not os.path.exists(LOG_DIR_PATH):
    os.mkdir(LOG_DIR_PATH)

#logging
logger = logging.getLogger("commands")
logger.setLevel(logging.ERROR)
file = os.path.join(LOG_DIR_PATH, "commands.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(message)s'))
logger.addHandler(handler)

loggerStart = logging.getLogger("start")
loggerStart.setLevel(logging.INFO)
file = os.path.join(LOG_DIR_PATH, "start.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(message)s'))
loggerStart.addHandler(handler)


intents = discord.Intents.none()
intents.members = True
intents.guilds = True

bot: Bot = Bot(intents=intents)
timeChecker = RoleTimeOutChecker(bot)
backup = BackupGenerator()

bot.add_cog(TimezoneCog(bot))
bot.add_cog(ShowCog(bot))
bot.add_cog(RemoveCog(bot))
bot.add_cog(AddCog(bot))

bot_start_time = bot_start_time = datetime.now(LOCAL_TIME_ZONE)
        
setup_done = False
@bot.event
async def on_ready():
    global bot_start_time
    global setup_done
    if not setup_done:
        try:
            loggerStart.info("The bot started in {} ".format( datetime.now(LOCAL_TIME_ZONE) - bot_start_time))
            print("We have logged in as {0.user}".format(bot))
            await database.create_database()
            
            await backup.backup_now(additional_info="_before_setup")
            loggerStart.info("Backup on start done")
            
            loggerStart.info("Bot in {} guilds. Guilds: {}".format(len(bot.guilds), bot.guilds))
        
            timeChecker.start()
            loggerStart.info("Time checker loop started successfully")
            
            await check_bot_still_in_server()
            # run in a other thread because is CPU heavy
            await asyncio.to_thread(check_for_member_changes)
                
            await backup.backup_now(additional_info="_after_setup")
            loggerStart.info("Backup on setup finish done")
            
            backup.start()
            loggerStart.info("Backup loop started successfully")
            
            loggerStart.info("All setup finish successfully")
        except Exception as error:
            loggerStart.exception("Error while starting up. Excepton {}".format(error))
        setup_done = True

def check_for_member_changes():
    start_time = datetime.now(LOCAL_TIME_ZONE)
    for member in bot.get_all_members():
        for role in member.roles:
            deltatime = database.get_time_role_deltatime_sync(role.id, member.guild.id)
            if deltatime is not None:
                deltatime = timedelta(seconds=deltatime)
                database.insert_member_time_role_sync(role.id, deltatime, member.id, member.guild.id)

    loggerStart.info("Changes in members setup finish. Took {}".format(datetime.now(LOCAL_TIME_ZONE) - start_time))

async def check_bot_still_in_server():
    start_time = datetime.now()
    nb_guild_deleted = await database.remove_unused_guild(bot)
    loggerStart.log(logging.INFO, "Changes in guilds setup finish. {} Guild deleted after {}".format(
        nb_guild_deleted, datetime.now() - start_time))

@bot.event
async def on_guild_join(guild: discord.Guild):
    loggerStart.log(logging.INFO, "Bot just joined {}. The bot is now in {} guilds.".format(guild, len(bot.guilds)))

@bot.event
async def on_guild_remove(guild: discord.Guild):
    loggerStart.log(logging.INFO, "Bot just left {}. The bot is now in {} guilds.".format(guild, len(bot.guilds)))
    await database.remove_guild(guild.id)
    
@bot.event  
async def on_guild_role_delete(role: discord.Role):
    # No need to remove role from members, because the on_member_update event will be trigger for each member who lost the role
    await database.remove_global_time_role(role.id, role.guild.id)
    await database.remove_server_time_role(role.id, role.guild.id)
    
@bot.event     
async def on_member_remove(member: discord.Member):
    await database.remove_member(member.id, member.guild.id)
      
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
async def on_member_update(before: discord.Member, after: discord.Member):
    before_roles = set(before.roles)
    after_roles = set(after.roles)
    
    deleted_roles = before_roles.difference(after_roles)
    added_roles = after_roles.difference(before_roles)
    
    for added_role in added_roles:
        deltatime = await database.get_time_role_deltatime(added_role.id, after.guild.id)
        if deltatime is not None:
            deltatime = timedelta(seconds=deltatime)
            await database.insert_member_time_role(added_role.id, deltatime, after.id, after.guild.id)
        
    for deleted_role in deleted_roles:
        await database.remove_member_time_role(deleted_role.id, after.id, after.guild.id)
        
    
@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: Exception):
    if isinstance(error, MissingPermissions):
        message = Message();
        message.addLine("Sorry {}, you do not have permissions to do that! You need to have manage_role permission".format(ctx.author.mention))
        embed = discord.Embed(title="Missing permissions", description=message.getString());
        await ctx.respond(embed=embed)
    else:
        error_id = datetime.now(tz=LOCAL_TIME_ZONE).strftime("%Y%m%d%H%M%S") + str(ctx.guild.id) + str(ctx.author.id)
        discord_message = """Your error code is {}
        If you want support show that error code in the Support server: {}
        Error: {}""".format(error_id, "https://discord.gg/hRTHpB4HUC", error)
        embed = discord.Embed(title="Something went wrong", color=0xFF0000, description=discord_message);
        embed.set_footer(text="If you wait to long, your error will be deleted from the logs")
        await ctx.respond(embed=embed)
        message = """id -> {}
        On guild {} by user {} 
        On command {} with values {}
        Error -> {}""".format(error_id, ctx.guild, ctx.author, ctx.command.name, ctx.selected_options, error)
        logger.error(message)

        
bot.run(TOKEN)