import discord
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)
from discord.ext import commands
from constant import guildIds
import database.database as database

class RemoveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @slash_command(guild_ids=guildIds, description="Remove a timed role of your server")     
    @discord.default_permissions(manage_roles=True)
    async def remove_timed_role_from_server(self, ctx: discord.ApplicationContext,
                                            role: discord.Option(discord.Role, "The time role to be remove from your server")):
        await ctx.defer()
        is_in = await database.is_time_role_in_database(role.id, ctx.guild_id)
        if is_in:
            await database.remove_server_time_role(role.id, ctx.guild_id)
            embed = discord.Embed(title="Remove successfull",
                                  description="The role {} was removed from the time role of the server !".format(role.mention))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Remove failed",
                color=0xFF0000,
                description="The time Role {} is not a server time role. run /show_timed_role_of_server to check what server timed role you have".format(role.mention))
            await ctx.respond(embed=embed)

    @slash_command(guild_ids=guildIds, description="Remove a global role from the server")    
    @discord.default_permissions(manage_roles=True)
    async def remove_global_timed_role(self, ctx: discord.ApplicationContext,
                                       role: discord.Option(discord.Role, "The global time role to be remove from your server")):
        await ctx.defer()
        is_in = await database.is_global_time_role_in_database(role.id, ctx.guild_id)
        if is_in:
            await database.remove_global_time_role(role.id, ctx.guild_id)
            embed = discord.Embed(title="Remove successfull",
                                  description="The global role {} was removed from the global timed role of the server !".format(role.mention))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Remove failed",
                color=0xFF0000,
                description="The global time Role {} is not a global time role. run /show_timed_role_of_server to check what global timed role you have".format(role.mention))
            await ctx.respond(embed=embed)


    @slash_command(guild_ids=guildIds, description="Remove a timed role from a user (not global time role)")      
    @discord.default_permissions(manage_roles=True)
    async def remove_timed_role_from_user(self, ctx, member: discord.Option(discord.Member, "The member that the role will be removed from"),
                                          role: discord.Option(discord.Role, "The time role to be remove from the member")):
        await ctx.defer()
        if role not in member.roles:
            embed = discord.Embed(
                title="Remove failed",
                color=0xFF0000,
                description="The user {} does not have the role {}".format(member.mention, role.mention))
            await ctx.respond(embed=embed)
            return
        
        isIn = await database.is_member_time_role_in_database(role.id, member.id, ctx.guild_id)

        if isIn:
            await database.remove_member_time_role(role.id, member.id, ctx.guild_id)
            await member.remove_roles(role)
            embed = discord.Embed(
            title="Remove Sucess",
            description="The time role {} was removed from the user {}".format(role.mention, member.mention))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
            title="Remove failed",
            color=0xFF0000,
            description="The user {} does not have the time role {}".format(member.mention, role.mention))
            await ctx.respond(embed=embed)
