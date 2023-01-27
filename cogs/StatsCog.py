from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database.database import Database

from discord import ApplicationContext, Embed, default_permissions, slash_command
from discord.commands import SlashCommandGroup
from discord.ext.commands import Cog
from constant import guildIds, DATABASE, ADMIN_COMMANDS_SERVER
import psutil
from os.path import dirname, isabs, abspath


class StatsCog(Cog):
    
    stats = SlashCommandGroup("stats", "Commands related to stats")
    
    
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.dabase = database
        self.database_path = DATABASE
        if not isabs(self.database_path):
            self.database_path = abspath(self.database_path)
        
    
    @stats.command(guild_ids=guildIds, description="Show the stats of the bot")      
    async def bot(self, ctx: ApplicationContext):
        await ctx.defer()
        embed = Embed(title=f"Stats of the bot")
        embed.add_field(name="Server count", value=f"{len(ctx.bot.guilds)} servers")
        embed.add_field(name="User count", value=f"{len(ctx.bot.users)/1000:,}k users")
        embed.add_field(name="Latency", value=f"{ctx.bot.latency * 1000:.2f} ms to discord")
        embed.add_field(name="CPU", value=f"{psutil.cpu_percent()} % used")
        embed.add_field(name="RAM", value=f"{psutil.virtual_memory()[2]:.2f} % used")
        disk_usage = psutil.disk_usage(dirname(self.database_path))
        embed.add_field(name="DISK", value=f"{disk_usage.percent} % used")
        embed.set_footer(text="If you like the bot, please consider supporting it at: https://ko-fi.com/champymarty_botdev")
        await ctx.respond(embed=embed)
        
    @stats.command(guild_ids=guildIds, description="Show the stats of your server")      
    async def server(self, ctx: ApplicationContext):
        await ctx.defer()
        embed = Embed(title=f"Stats of {ctx.guild.name}")
        
        nb_time_roles_server = await self.dabase.get_server_time_roles_counts(ctx.guild_id)
        embed.add_field(name="Server time role count", value=f"{nb_time_roles_server} roles")
        
        nb_time_roles_global = await self.dabase.get_global_time_roles_counts(ctx.guild_id)
        embed.add_field(name="Global time role count", value=f"{nb_time_roles_global} roles")
        
        nb_time_roles = await self.dabase.get_time_roles_counts(ctx.guild_id)
        embed.add_field(name="Time role count", value=f"{nb_time_roles} roles")
        
        embed.set_footer(text="If you like the bot, please consider supporting it at: https://ko-fi.com/champymarty_botdev")
        await ctx.respond(embed=embed)
        
    @slash_command(guild_ids=ADMIN_COMMANDS_SERVER, description="Show the admin stats")
    @default_permissions(administrator=True) 
    async def admin_stats(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=True)
        embed = Embed(title=f"Stats of all")
        
        count_no_0_1, count_1 = await self.dabase.get_server_time_roles_counts_avg()
        count_no_0_2, count_2  = await self.dabase.get_global_time_roles_counts_avg()
        count_no_0_3, count_3  = await self.dabase.get_time_roles_counts_avg()
        
        embed.add_field(name="Server time role count(!=0)", value=f"{count_no_0_1} roles avg no 0")
        embed.add_field(name="Global time role count(!=0)", value=f"{count_no_0_2} roles avg no 0")
        embed.add_field(name="Time role count(!=0)", value=f"{count_no_0_3} roles avg no 0")
        
        embed.add_field(name="Server time role count", value=f"{count_1} roles avg")
        embed.add_field(name="Global time role count", value=f"{count_2} roles avg")
        embed.add_field(name="Time role count", value=f"{count_3} roles avg")
        
        await ctx.respond(embed=embed, ephemeral=True)