from discord import ApplicationContext, Role, Member
from discord.ext.commands import Cog
from database.database import Database
from exceptions.BotNotReadyException import BotNotReadyException
from exceptions.MissingManageRoleException import MissingManageRoleException
from exceptions.UnderRoleHierarchyException import UnderRoleHierarchyException

class WriteCog(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database: Database = self.bot.database

    async def cog_before_invoke(self, ctx: ApplicationContext) -> None:
        role_id = None
        for option in ctx.selected_options:
            if option.get("type") == 8:
                role_id = option.get("value")
                break
        if role_id is None or "":
            return
        role, network_error = await self.bot.get_or_fetch_role(ctx.guild, int(role_id))
        self.check_role_hierarchy(ctx, role)
        self.check_for_manage_role(ctx)
        self.check_for_bot_ready()
        
    def check_role_hierarchy(self, ctx: ApplicationContext, role: Role) -> bool:
        myBot: Member = ctx.guild.get_member(self.bot.user.id)
        if myBot.top_role.position > role.position:
            return
        raise UnderRoleHierarchyException(role)
    
    def check_for_manage_role(self, ctx: ApplicationContext) -> bool:
        my_bot: Member = ctx.guild.get_member(self.bot.user.id)
        if not my_bot.guild_permissions.manage_roles:
            raise MissingManageRoleException()
        
    def check_for_bot_ready(self) -> bool:
        if not self.bot.bot_can_start_write_commands:
            raise BotNotReadyException()    