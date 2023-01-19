import sqlite3
from typing import Any
from discord.ext.commands import Bot as discord_bot
from BackupGenerator import BackupGenerator
from MarkdownDiscord import Message
from RoleTimeOutChecker import RoleTimeOutChecker
from cogs.AddCog import AddCog
from cogs.RemoveCog import RemoveCog
from cogs.ShowCog import ShowCog
from cogs.StatsCog import StatsCog
from cogs.TimezoneCog import TimezoneCog
from database.database import Database
import logging
from aiohttp.client_exceptions import ClientConnectorError
from datetime import datetime
from asyncio import to_thread
import discord
from discord.ext.commands.errors import MissingPermissions
from constant import DATABASE, LOCAL_TIME_ZONE
from constant import datetime_strptime

class TimeRoleBot(discord_bot):
    
    def __init__(self, **options):
        super().__init__(**options)
        self.database: Database  = Database()
        
        self.timeChecker = RoleTimeOutChecker(self)
        self.backup = BackupGenerator(self.database)
        
        self.start_logger: logging.Logger = logging.getLogger("start")
        self.command_logger: logging.Logger = logging.getLogger("commands")
        self.event_logger: logging.Logger = logging.getLogger("bot_events")
        
        self.addCog = AddCog(self)
        
        self.add_cog(TimezoneCog(self))
        self.add_cog(ShowCog(self))
        self.add_cog(self.addCog)
        self.add_cog(RemoveCog(self))
        self.add_cog(StatsCog(self.database))
        
        self.setup_done = False
        self.bot_can_start_write_commands = False
        self.bot_start_time = None
        
    async def on_resumed(self):
        self.start_logger.info("Reconnect to discord")
        await self.check_bot_still_in_server()
        # run in a other thread because is CPU heavy
        start_time = datetime.now(LOCAL_TIME_ZONE)   
        inserts = await to_thread(self.check_for_member_changes)
        if len(inserts) > 0:
            await self.database.insert_all_member_time_role(inserts)
            await self.database.commit()
        self.start_logger.info("Changes in members setup finish. Added {} rows.  Took {}".format(
            len(inserts), datetime.now(LOCAL_TIME_ZONE) - start_time))
        
    async def on_connect(self):
        self.bot_start_time = datetime.now(LOCAL_TIME_ZONE)
        await self.database.connect()
        await self.database.create_database_if_not_exist()
        return await super().on_connect()
        
    async def on_ready(self):
        if not self.setup_done:
            try:
                self.start_logger.info("The bot started in {} ".format( datetime.now(LOCAL_TIME_ZONE) - self.bot_start_time))
                print("We have logged in as {0.user}".format(self))
                
                await self.backup.backup_now(additional_info="_before_setup")
                self.start_logger.info("Backup on start done")
                
                self.start_logger.info("Bot in {} guilds. Guilds: {}".format(len(self.guilds), self.guilds))
            
                self.timeChecker.start()
                self.start_logger.info("Time checker loop started successfully")
                
                await self.check_bot_still_in_server()
                self.bot_can_start_write_commands = True
                
                # run in a other thread because is CPU heavy
                start_time = datetime.now(LOCAL_TIME_ZONE)   
                inserts = await to_thread(self.check_for_member_changes)
                if len(inserts) > 0:
                    await self.database.insert_all_member_time_role(inserts)
                    await self.database.commit()
                self.start_logger.info("Changes in members setup finish. Added {} rows.  Took {}".format(
                    len(inserts), datetime.now(LOCAL_TIME_ZONE) - start_time))
                    
                await self.backup.backup_now(additional_info="_after_setup")
                self.start_logger.info("Backup on setup finish done")
                
                self.backup.start()
                self.start_logger.info("Backup loop started successfully")
                
                self.start_logger.info("All setup finish successfully")
            except Exception as error:
                self.start_logger.exception("Error while starting up. Excepton {}".format(error))
            self.setup_done = True
            
    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        self.event_logger.exception(f"Error on method {event_method} \nargs  {args} \nkwargs{kwargs}")
        return await super().on_error(event_method, *args, **kwargs)
            
    async def on_guild_join(self, guild: discord.Guild):
        self.start_logger.log(logging.INFO, "Bot just joined {}. The bot is now in {} guilds.".format(guild, len(self.guilds)))

    async def on_guild_remove(self, guild: discord.Guild):
        self.start_logger.log(logging.INFO, "Bot just left {}. The bot is now in {} guilds.".format(guild, len(self.guilds)))
        await self.database.remove_guild(guild.id, commit=True)
        
    async def on_guild_role_delete(self, role: discord.Role):
        # No need to remove role from members, because the on_member_update event will be trigger for each member who lost the role
        await self.database.remove_global_time_role(role.id, role.guild.id)
        await self.database.remove_server_time_role(role.id, role.guild.id)
        
    async def on_member_remove(self, member: discord.Member):
        await self.database.remove_member(member.id, member.guild.id)
        
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        
        deleted_roles = before_roles.difference(after_roles)
        added_roles = after_roles.difference(before_roles)
        
        for added_role in added_roles:
            deltatime = await self.database.get_time_role_deltatime(added_role.id, after.guild.id)
            if deltatime is not None:
                await self.database.insert_member_time_role(added_role.id, deltatime, after.id, after.guild.id)
            
        for deleted_role in deleted_roles:
            await self.database.remove_member_time_role(deleted_role.id, after.id, after.guild.id)
            
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception):
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
            self.command_logger.error(message)
            
    def check_for_member_changes(self):
        inserts = []
        with sqlite3.connect(DATABASE) as db:
            for member in self.get_all_members():
                for role in member.roles:
                    deltatime = self.database.get_time_role_deltatime_sync(db, role.id, member.guild.id)
                    if deltatime is not None:
                        if not self.database.is_member_time_role_in_database_sync(db, role.id, member.id, member.guild.id):
                            inserts.append((role.id, datetime.now().strftime(datetime_strptime), 
                                            deltatime.total_seconds(), member.id,  member.guild.id))
        return inserts

    async def check_bot_still_in_server(self):
        start_time = datetime.now()
        nb_guild_deleted = 0
        nb_guild_deleted = await self.database.remove_unused_guild(self)
        self.start_logger.log(logging.INFO, "Changes in guilds setup finish. {} Guild deleted after {}".format(
            nb_guild_deleted, datetime.now() - start_time))
        
    async def get_or_fetch_role(self, guild: discord.Guild, role_id: int):
            role_get = guild.get_role(role_id)
            if role_get is None:
                try:
                    role_get: discord.Role = await guild._fetch_role(role_id) 
                except ClientConnectorError:
                    return (None, True)
                except:
                    return (None, False)
            return (role_get, False)
        
    async def get_or_fetch_member(self, guild: discord.Guild, member_id: int):
        member = guild.get_member(member_id)
        if member is None:
            try:
                member = await guild.fetch_member(member_id)
            except ClientConnectorError:
                return (None, True)
            except:
                return (None, False)
        return (member, False)

    async def get_or_fetch_guild(self, guild_id: int):
        guild = self.get_guild(guild_id)
        if guild is None:
            try:
                guild = await self.fetch_guild(guild_id)
            except ClientConnectorError:
                return (None, True)
            except:
                return (None, False)
        return (guild, False)

    async def get_or_fetch_guild_member_role(self, guild_id: int, member_id: int, role_id: int):
        guild, network_error = await self.get_or_fetch_guild(guild_id)
        if guild is None:
            return (None, None, None, network_error)
        member, network_error = await self.get_or_fetch_member(guild, member_id)
        if member is None:
            return (guild, None, None, network_error)
        role, network_error = await self.get_or_fetch_role(guild, role_id)
        if role is None:
            return (guild, member, None, network_error)
        return (guild, member, role, network_error)
        
    async def close(self) -> None:
        await self.database.close()
        return await super().close()
    