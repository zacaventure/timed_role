from discord import ApplicationContext, Role, Member, Embed
from discord.ext.commands import Cog
from database.database import Database

class WriteCog(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database: Database = self.bot.database
        
    async def check_for_bot_permissions_and_hierarchie(self, ctx: ApplicationContext, role: Role) -> bool:
        if not await self.check_for_manage_role(ctx):
            return False
        if not await self.check_for_role_order(ctx, role):
            return False
        return True
        
    def canTheBotHandleTheRole(self, ctx: ApplicationContext, role: Role) -> bool:
        myBot: Member = ctx.guild.get_member(self.bot.user.id)
        if myBot.top_role.position > role.position:
            return True
        return False
    
    async def check_for_role_order(self, ctx: ApplicationContext, role: Role) -> bool:
        if not self.canTheBotHandleTheRole(ctx, role):
            embed = Embed(
                title="Bot is under in the roles hierarchie",
                color=0xFF0000,
                description=f"The role {role.mention} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role")
            await ctx.respond(embed=embed)
            return False
        return True
    
    def have_manage_role(self, ctx: ApplicationContext) -> bool:
        my_bot: Member = ctx.guild.get_member(self.bot.user.id)
        return my_bot.guild_permissions.manage_roles
    
    async def check_for_manage_role(self, ctx: ApplicationContext) -> bool:
        """Check for if the bot has the manage roles permission. If not, send a error message to
            the user of the command with ctx.respond()
            
            Return True if the bot as the manage_roles permission, else return False
        """
        if not self.have_manage_role(ctx):
            embed = Embed(
                title="The bot is missing the manage_roles permissions on your server",
                color=0xFF0000,
                description=f"Please give the bot the permission, otherwise the bot cant add/remove that roles from users")
            await ctx.respond(embed=embed)
            return False
        return True
        
    async def check_for_bot_ready(self, ctx: ApplicationContext) -> bool:
        if not self.bot.bot_can_start_write_commands:
            embed = Embed(
                title="Bot is booting up",
                color=0xFF0000,
                description=f"Please wait for the bot to be ready, it won't take long")
            await ctx.respond(embed=embed)
            return False
        return True
    