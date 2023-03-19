import discord
from discord import ApplicationContext, Color, Member, Role, SlashCommandGroup, option, Option
from cogs.WriteCog import WriteCog
from constant import guildIds

class RemoveCog(WriteCog):
    def __init__(self, bot):
        super().__init__(bot)

    REMOVE_GROUP = SlashCommandGroup("remove", "Command group to remove various timed role types")
        
    @REMOVE_GROUP.command(guild_ids=guildIds, name="server_timed_role", description="Remove a timed role of your server")     
    @discord.default_permissions(manage_roles=True)
    @option(
        "role",
        description="The time role to be remove from your server",
        type=Role
    )
    async def remove_timed_role_from_server(self, ctx: ApplicationContext, role: Role):
        await ctx.defer()
        is_in = await self.database.is_time_role_in_database(role.id, ctx.guild_id)
        if is_in:
            await self.database.remove_server_time_role(role.id, ctx.guild_id)
            embed = discord.Embed(title="Remove successfull",
                                  color=Color.green(),
                                  description="The role {} was removed from the time role of the server !".format(role.mention))
            await self.database.commit()
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Remove failed",
                color=0xFF0000,
                description="The time Role {} is not a server time role. run /show_timed_role_of_server to check what server timed role you have".format(role.mention))
            await ctx.respond(embed=embed)

    @REMOVE_GROUP.command(guild_ids=guildIds, name="global_timed_role", description="Remove a global role from the server")    
    @discord.default_permissions(manage_roles=True)
    @option(
        "role",
        description="The global time role to be remove from your server",
        type=Role
    )
    async def remove_global_timed_role(self, ctx: ApplicationContext, role: Role):
        await ctx.defer()
        is_in = await self.database.is_global_time_role_in_database(role.id, ctx.guild_id)
        if is_in:
            await self.database.remove_global_time_role(role.id, ctx.guild_id)
            embed = discord.Embed(title="Remove successfull",
                                  color=Color.green(),
                                  description="The global role {} was removed from the global timed role of the server !".format(role.mention))
            await self.database.commit()
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Remove failed",
                color=0xFF0000,
                description="The global time Role {} is not a global time role. run /show_timed_role_of_server to check what global timed role you have".format(role.mention))
            await ctx.respond(embed=embed)


    @REMOVE_GROUP.command(guild_ids=guildIds, name="timed_role_from_user", description="Remove a timed role from a user (not global time role)")      
    @discord.default_permissions(manage_roles=True)
    async def remove_timed_role_from_user(self, ctx, member: Option(Member, "The member that the role will be removed from"),
                                          role: Option(Role, "The time role to be remove from the member")):
        await ctx.defer()
        if role not in member.roles:
            embed = discord.Embed(
                title="Remove failed",
                color=0xFF0000,
                description="The user {} does not have the role {}".format(member.mention, role.mention))
            await ctx.respond(embed=embed)
            return
        
        isIn = await self.database.is_member_time_role_in_database(role.id, member.id, ctx.guild_id)

        if isIn:
            await self.database.remove_member_time_role(role.id, member.id, ctx.guild_id)
            await member.remove_roles(role)
            embed = discord.Embed(
                title="Remove Sucess",
                color=Color.green(),
                description="The time role {} was removed from the user {}".format(role.mention, member.mention))
            await self.database.commit()
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
            title="Remove failed",
            color=0xFF0000,
            description="The user {} does not have the time role {}".format(member.mention, role.mention))
            await ctx.respond(embed=embed)

    @REMOVE_GROUP.command(guild_ids=guildIds, name="recurrent_timed_role", description="Remove a recurrent timed role")
    @discord.default_permissions(manage_roles=True)
    @option(
        "role",
        description="Enter the recurrent time role to remove",
        type=Role
    )
    async def remove_recurrent_time_role(self, ctx: ApplicationContext, role: Role):
        recurrent_role = await self.database.get_recurrent_time_role(role.id, ctx.guild_id)
        if recurrent_role is None:
            embed = discord.Embed(
                title="Could not remove the role",
                color=0xFF0000,
                description=f"The role {role.mention} does not exist in the database as a recurrent time role")
        else:
            await self.database.remove_recurrent_time_role(role.id, ctx.guild_id)
            await self.database.commit()
            embed = discord.Embed(title="Remove successfull",
                                  color=discord.Color.green(),
                                  description=f"The recurrent time role {role.mention} was removed from the database !")
        await ctx.respond(embed=embed)
