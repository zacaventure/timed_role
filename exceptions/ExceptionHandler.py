from datetime import datetime
import logging
import traceback
from discord import ApplicationContext, DiscordException, Embed
from discord.ext.commands.errors import MissingPermissions
from constant import LOCAL_TIME_ZONE, SUPPORT_SERVER_INVITE_URL
from exceptions.BotNotReadyException import BotNotReadyException
from exceptions.MissingManageRoleException import MissingManageRoleException


from exceptions.UnderRoleHierarchyException import UnderRoleHierarchyException
from utils.MarkdownDiscord import Message


class ExceptionHandler:
    def __init__(self, ctx: ApplicationContext, exception: DiscordException) -> None:
        self.ctx = ctx
        self.discord_exception: DiscordException = exception
        self.command_logger = logging.Logger = logging.getLogger("commands")

    async def _handle_unknown(self) -> None:
        error_id = datetime.now(tz=LOCAL_TIME_ZONE).strftime("%Y%m%d%H%M%S") + str(self.ctx.guild.id) + str(self.ctx.author.id)
        discord_message = f"""Your error code is {error_id}
        If you want support show that error code in the Support server: {SUPPORT_SERVER_INVITE_URL}
        Error: {self.discord_exception}"""
        embed = Embed(title="Something went wrong", color=0xFF0000, description=discord_message);
        embed.set_footer(text="If you wait to long, your error will be deleted from the logs")
        await self.ctx.respond(embed=embed)
        message = f"""id -> {error_id}
        On guild {self.ctx.guild} by user {self.ctx.author} 
        On command {self.ctx.command.name} with values {self.ctx.selected_options}
        Error -> {self.discord_exception}
        Original -> {"".join(traceback.format_tb(self.discord_exception.original.__traceback__))}"""
        self.command_logger.exception(message)


    async def handle(self) -> None:
        error_handled = await self._handle_custom_exceptions()
        if error_handled:
            return
        
        if isinstance(self.discord_exception, MissingPermissions):
            return await self._handle_missing_permissions()
        return await self._handle_unknown()
    
    async def _handle_custom_exceptions(self) -> bool:
        if isinstance(self.discord_exception.original, UnderRoleHierarchyException):
            await self._handle_hierarchy()
            return True
        if isinstance(self.discord_exception.original, MissingManageRoleException):
            await self._handle_missing_manage_role()
            return True
        if isinstance(self.discord_exception.original, BotNotReadyException):
            await self._handle_bot_not_ready()
            return True
        return False

    async def _handle_missing_permissions(self) -> None:
        message = Message();
        message.addLine(f"Sorry {self.ctx.author.mention}, you do not have permissions to do that! You need to have manage_role permission")
        embed = Embed(title="Missing permissions", description=message.getString());
        await self.ctx.respond(embed=embed)

    async def _handle_bot_not_ready(self) -> None:
        embed = Embed(
            title="Bot is booting up",
            color=0xFF0000,
            description=f"Please wait for the bot to be ready, it won't take long")
        await self.ctx.respond(embed=embed)
    
    async def _handle_hierarchy(self) -> None:
        exception: UnderRoleHierarchyException = self.discord_exception.original
        embed = Embed(
            title="Bot is under in the roles hierarchie",
            color=0xFF0000,
            description=f"The role {exception.role.mention} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role")
        await self.ctx.respond(embed=embed)

    async def _handle_missing_manage_role(self) -> None:
        embed = Embed(
            title="The bot is missing the manage_roles permissions on your server",
            color=0xFF0000,
            description=f"Please give the bot the permission, otherwise the bot cant add/remove that roles from users")
        await self.ctx.respond(embed=embed)

