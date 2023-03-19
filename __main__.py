import discord
from timeRoleBot import TimeRoleBot
from constant import TOKEN, guildIds
from loggers import createLoggers
from cogs.Util import have_internet
from time import sleep

from utils.MarkdownDiscord import Message

createLoggers()

intents = discord.Intents.none()
intents.members = True
intents.guilds = True

bot: TimeRoleBot = TimeRoleBot(intents=intents)

def add_individual_roles_field(embed: discord.Embed, commands: dict[str, discord.SlashCommand]) -> None:
    name = "__Individual Roles__ (bot need manage_role permission)"
    individual_roles_description = Message()
    add_update_command = commands.get("add-update time_role")
    remove_command = commands.get("remove timed_role_from_user")
    individual_roles_description.addLine(
        f"Individual timed roles apply only to one person at a time. You can manually create a new timed role to \
            add to a user with the command {add_update_command.mention}. If you use this command only that member will get \
                a timed role with a certain number of days,hours and minutes before it disappears.")
    
    individual_roles_description.addLine(f"You can also remove a timed role to a user with {remove_command.mention}")
    embed.add_field(name=name, value=individual_roles_description.getString())

def add_server_roles_field(embed: discord.Embed, commands: dict[str, discord.SlashCommand]) -> None:
    name = "__Server timed Roles__ (bot need manage_role permission)"
    description = Message()
    add_update_command = commands.get("add-update server_time_role")
    remove_command = commands.get("remove server_timed_role")
    show_command = commands.get("show server_timed_roles")
    description.addLine(
        f"Server timed roles are similar to individual timed role but they can be automatize. By doing the command \
              {add_update_command.mention}, you are adding a timed role for the server with a number of days of expiration \
                (with also hours and minutes as option parameters). Any member of the server getting the role will be given \
                    an individual timed role with the expiration time specified in the server time role.")
    
    description.addLine(f"You can also remove a server timed role with {remove_command.mention}")
    description.addLine(f"You can also see all server timed role with {show_command.mention}")
    embed.add_field(name=name, value=description.getString())

def add_global_roles_field(embed: discord.Embed, commands: dict[str, discord.SlashCommand]) -> None:
    name = "__Global timed Roles__ (bot need manage_role permission)"
    description = Message()
    add_update_command = commands.get("add-update global_timed_role")
    remove_command = commands.get("remove global_timed_role")
    show_command = commands.get("show global_timed_roles")
    timezone_set = commands.get("timezone set")
    description.addLine(
        f"Global timed roles are role that are deleted in the server at a specifed date and time. By doing the command \
              {add_update_command.mention}, you are adding a global timed role with expiration date and time. \
                When the date and time is reached, the role is deleted from the server. You can set your timezone \
                    for your date and time using the command {timezone_set.mention}")
    
    description.addLine(f"You can also remove a global timed role with {remove_command.mention}")
    description.addLine(f"You can also see all global timed role with {show_command.mention}")
    embed.add_field(name=name, value=description.getString(), inline=False)

def add_recurrent_roles_field(embed: discord.Embed, commands: dict[str, discord.SlashCommand]) -> None:
    name = "__Recurrent timed Roles__ (bot need manage_role permission)"
    description = Message()
    add_update_command = commands.get("add-update recurrent_timed_role")
    remove_command = commands.get("remove recurrent_timed_role")
    show_command = commands.get("show recurrent_timed_roles")
    timezone_set = commands.get("timezone set")
    description.addLine(
        f"Recurrent timed roles are role that are removed from every member at a specific time interval (example: each day). \
            By doing the command {add_update_command.mention}, you are adding a recurrent timed role with a start date-time \
            and a interval to which the role will be removed. You can set your timezone \
                    for your date and time using the command {timezone_set.mention}")
    
    description.addLine(f"You can also remove a recurrent timed role with {remove_command.mention}")
    description.addLine(f"You can also see all recurrent timed role with {show_command.mention}")
    embed.add_field(name=name, value=description.getString(), inline=True)

def add_timezone_field(embed: discord.Embed, commands: dict[str, discord.SlashCommand]) -> None:
    name = "__Timezones__"
    description = Message()
    set_command = commands.get("timezone set")
    show_command = commands.get("timezone show")
    description.addLine(
        f"You can set your timezone with the command {set_command.mention}. The available timezone can be found \
            [here](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568). You can also check \
                the timezone of your server with the command {show_command.mention}")
    embed.add_field(name=name, value=description.getString(), inline=True)

def add_show_field(embed: discord.Embed, commands: dict[str, discord.SlashCommand]) -> None:
    name = "__Displaying your server info__"
    description = Message()
    show_all = commands.get("show all")
    show_member = commands.get("show member")
    show_role = commands.get("show role")
    description.addLine(f"You can use the command {show_all.mention} to display all the timed roles types of your server")
    description.addLine(f"You can use the command {show_member.mention} to display all the timed roles of a member")
    description.addLine(f"You can use the command {show_role.mention} to display all the members of a timed role")
    embed.add_field(name=name, value=description.getString(), inline=False)
      
@bot.slash_command(guild_ids=guildIds, pass_context = True, description="Show help window")
async def help(ctx):
    await ctx.defer()
    commands = bot.get_commands_as_dict()

    embed = discord.Embed(title="Help for the bot !")
    add_individual_roles_field(embed, commands)
    add_server_roles_field(embed, commands)
    add_global_roles_field(embed, commands)
    add_recurrent_roles_field(embed, commands)
    add_timezone_field(embed, commands)
    add_show_field(embed, commands)

    await ctx.respond(embed=embed)

def wait_for_internet():
    is_connected = False
    while not is_connected:
        is_connected = have_internet()
        if is_connected:
            return
        sleep(5)
        
wait_for_internet()
bot.run(TOKEN)