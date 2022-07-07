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
    async def remove_timed_role_from_server(self, ctx, role: discord.Option(discord.Role, "The time role to be remove from your server")):
        await ctx.defer()
        server = self.data.getServer(ctx.guild.id)
        if role.id in server.timedRoleOfServer:
            del server.timedRoleOfServer[role.id]
            for member in server.members:
                pos = 0
                for timedRole in member.timedRole:
                    if timedRole.roleId == role.id:
                        del member.timedRole[pos]
                    pos += 1             
            self.data.saveData()
            await ctx.respond("The role was removed from the server !")
        else:
            await ctx.respond("The role is not a timed role of the server !")

    @slash_command(guild_ids=guildIds, description="Remove a global role from the server")    
    @discord.default_permissions(manage_roles=True)
    async def remove_global_timed_role(self, ctx, role: discord.Option(discord.Role, "The global time role to be remove from your server")):
        await ctx.defer()
        server = self.data.getServer(ctx.guild.id)
        i = 0
        found=False
        for globalTimeRole in server.globalTimeRoles:
            if globalTimeRole.roleId == role.id:
                found=True
                break
            i += 1
        if found:
            del server.globalTimeRoles[i]
            self.data.saveData()
            await ctx.respond("The global role was removed from the server !")
        else:
            await ctx.respond("This global time Role do not exist. run /show_timed_role_of_server to check what global timed role you have")

    @slash_command(guild_ids=guildIds, description="Remove a timed role from a user (not global time role)")      
    @discord.default_permissions(manage_roles=True)
    async def remove_timed_role_from_user(self, ctx, member: discord.Option(discord.Member, "The member that the role will be removed from"),
                                          role: discord.Option(discord.Role, "The time role to be remove from the member")):
        await ctx.defer()
        memberData = self.data.getMember(member.guild.id, member.id)
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
        await ctx.respond("Custom role remove !")            