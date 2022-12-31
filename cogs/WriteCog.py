from discord import ApplicationContext, Role, Member
from discord.ext.commands import Cog
from database.database import Database

class WriteCog(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database: Database = self.bot.database
        
    def canTheBotHandleTheRole(self, ctx: ApplicationContext, role: Role) -> bool:
        myBot: Member = ctx.guild.get_member(self.bot.user.id)
        if myBot.top_role.position > role.position:
            return True
        return False