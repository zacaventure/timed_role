from discord import ApplicationContext, Role, Option, User, Embed, File, Colour
from discord.commands import slash_command
import os
from discord.ext.commands import Cog
from constant import guildIds, RES_PATH



class SupportCog(Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    @slash_command(guild_ids=guildIds, description="Show information about donating")
    async def donate(self, ctx: ApplicationContext):
        await ctx.defer()
        creator: User = await self.bot.get_or_fetch_user(196751144209481733)
        img_path = os.path.join(RES_PATH, "credit.png")
        file = File(img_path, filename="credit.png")
        
        link = "[Donation page](https://ko-fi.com/champymarty_botdev)"
        donating = Embed(title="Donation FAQ", description=f"Hello there ! Here is my {link}",
                         color=Colour(int("3d40e3", 16)))
        donating.set_image(url=f"attachment://{file.filename}")
        donating.set_author(name=creator.display_name, icon_url=creator.display_avatar.url)
        donating.add_field(name="Why donate ?", value="If you find this bot useful and would like to contribute to its development, please consider donating. It is definitely not mandatory, but your support is very appreciated.")
        donating.add_field(name="What will it be used for ?", value="As some of you know, this is a passion project. I run these bots at home. With the money, I plan to have a more stable server, so the bot can be run smoothly and with more stability. In addition, running the bot comes at a cost, which I am paying with my own money")
        donating.set_footer(text="As always, I thank you from the bottom of my heart for your support, it really means a lot to me",
                            icon_url=ctx.bot.user.display_avatar)
        await ctx.respond(file=file, embed=donating)
        
    @slash_command(guild_ids=guildIds, description="Vote for the bot on top.gg")
    async def vote(self, ctx: ApplicationContext):
        await ctx.defer()
        creator: User = await self.bot.get_or_fetch_user(196751144209481733)
        img_path = os.path.join(RES_PATH, "yoimiya.png")
        file = File(img_path, filename="yoimiya.png")
        link = "[Here](https://top.gg/bot/925497481423384656/vote)"
        donating = Embed(title="Voting !", description=f"Support {ctx.me.mention} by voting {link}!",
                         color=Colour(int("3d40e3", 16)))
        donating.set_image(url=f"attachment://{file.filename}")
        donating.set_author(name=creator.display_name, icon_url=creator.display_avatar.url)
        donating.set_footer(text="As always, I thank you from the bottom of my heart for your support, it really means a lot to me",
                            icon_url=ctx.bot.user.display_avatar)
        await ctx.respond(file=file, embed=donating)
        
    @slash_command(guild_ids=guildIds, description="Reviews for the bot on top.gg")
    async def review(self, ctx: ApplicationContext):
        await ctx.defer()
        creator: User = await self.bot.get_or_fetch_user(196751144209481733)        
        link = "[Here](https://top.gg/bot/925497481423384656#reviews)"
        donating = Embed(title="Reviews !", description=f"Support {ctx.me.mention} by reviewing {link}!",
                         color=Colour(int("3d40e3", 16)))
        donating.set_author(name=creator.display_name, icon_url=creator.display_avatar.url)
        donating.set_footer(text="As always, I thank you from the bottom of my heart for your support, it really means a lot to me",
                            icon_url=ctx.bot.user.display_avatar)
        await ctx.respond(embed=donating)