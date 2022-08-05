import discord
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)
from discord.ext import commands
from constant import guildIds
from data import Data

class RemoveCog(commands.Cog):
    def __init__(self, bot, data: Data):
        self.bot = bot
        self.data = data
        
    @slash_command(guild_ids=guildIds, description="Remove a timed role of your server")     
    @discord.default_permissions(manage_roles=True)
    async def remove_timed_role_from_server(self, ctx: discord.ApplicationContext,
                                            role: discord.Option(discord.Role, "The time role to be remove from your server")):
        await ctx.defer()
        server = self.data.getServer(ctx.guild.id)
        if role.id in server.timedRoleOfServer:
            self.data.delete_time_role(role.id, ctx.guild.id, server=server, remove_global=False)
            embed = discord.Embed(title="Remove successfull",
                                  description="The role {} was removed from the time role of the server !".format(role.mention))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Remove failed",
                description="The time Role {} is not a server time role. run /show_timed_role_of_server to check what server timed role you have".format(role.mention))
            await ctx.respond(embed=embed)

    @slash_command(guild_ids=guildIds, description="Remove a global role from the server")    
    @discord.default_permissions(manage_roles=True)
    async def remove_global_timed_role(self, ctx: discord.ApplicationContext,
                                       role: discord.Option(discord.Role, "The global time role to be remove from your server")):
        await ctx.defer()
        if self.data.delete_time_role(role.id, ctx.guild.id, remove_server=False, remove_role_in_members=False):
            embed = discord.Embed(title="Remove successfull",
                                  description="The global role {} was removed from the global timed role of the server !".format(role.mention))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Remove failed",
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
                description="The user {} does not have the role {}".format(member.mention, role.mention))
            await ctx.respond(embed=embed)
            return
        server = self.data.getServer(member.guild.id)
        memberData = self.data.getMember(member.guild.id, member.id, server=server)
        if role.id in server.timedRoleOfServer:
            await member.remove_roles(role)
            embed = discord.Embed(
                title="Remove Sucess",
                description="The time role {} was removed from the user {}".format(role.mention, member.mention))
            await ctx.respond(embed=embed)
            return
        i = 0
        isIn = False
        for timeRole in memberData.timedRole:
            if timeRole.roleId == role.id:
                isIn = True
                break
            i += 1
        if isIn:
            del memberData.timedRole[i]
            self.data.saveData()
            await member.remove_roles(role)
            embed = discord.Embed(
            title="Remove Sucess",
            description="The time role {} was removed from the user {}".format(role.mention, member.mention))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
            title="Remove failed",
            description="The user {} does not have the time role {}".format(member.mention, role.mention))
            await ctx.respond(embed=embed)
