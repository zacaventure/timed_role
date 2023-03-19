from __future__ import annotations
from typing import TYPE_CHECKING
from utils.MarkdownDiscord import Message
if TYPE_CHECKING:
    from database.database import Database
import discord
from discord import InputTextStyle, Role
from datetime import timedelta, date, datetime
import pytz


def generate_edit_embed(mention: str, start_datetime: datetime, delta: timedelta, timezone: str, next_datetime: datetime):
    if timezone is None:
        timezone = "not set"
    description = Message()
    description.addLine("That role currently already exists as a recurrent timed role.").nextLine()

    description.addLine(f"Current value: **delete the role {mention} starting at {start_datetime.date()} at {start_datetime.time()} each {delta}** in {timezone} timezone")
    description.nextLine()
    description.addLine("Editing is currently **not supported**, please delete and re-add the role if you want to change it")
    description.nextLine()

    description.addLine("Next removal dates: ")
    for i in range(3):
        description.addLine(f"{i+1}) {next_datetime + (i * delta)}")
    return discord.Embed(
        title="Update a recurrent timed role",
        description=description.getString()
    )

def generate_insert_embed(mention: str, start_datetime: datetime, delta: timedelta, timezone: str, approved=False):
    if timezone is None:
        timezone = "not set"
    description = Message()
    description.addLine("Use the button to set information.").nextLine()

    description.addLine(f"Current value: **delete the role {mention} starting at {None if start_datetime is None else start_datetime.date()} at {timedelta(seconds=0) if start_datetime is None else start_datetime.time()} each {delta}** in {timezone} timezone")
    description.nextLine()

    if start_datetime is not None and delta is not None:
        description.addLine("Next removal dates: ")
        for i in range(3):
            description.addLine(f"{i+1}) {start_datetime + (i * delta)}")
        description.nextLine()
    
    if approved:
        description.addLine("The role got __**approved**__ !" )
    return discord.Embed(
        title="Create a recurrent timed role",
        description=description.getString()
    )

class InputText(discord.ui.InputText):
    def __init__(self, *, style: InputTextStyle = InputTextStyle.short, custom_id: str | None = None, label: str,
                 placeholder: str | None = None, min_length: int | None = None, max_length: int | None = None,
                 required: bool | None = True, value: str | None = None, row: int | None = None, key: str = None):
        super().__init__(style=style, custom_id=custom_id,
                         label=label, placeholder=placeholder, min_length=min_length,
                         max_length=max_length, required=required, value=value, row=row,)
        self.key = key
    

class Modal(discord.ui.Modal):
    def __init__(self, *children, title: str, custom_id: str | None = None, timeout: float | None = None, update_co=None, data: dict = None) -> None:
        super().__init__(*children, title=title, custom_id=custom_id, timeout=timeout)
        self.data = data
        if self.data is None:
            self.data = dict()
        self.update_co = update_co
        
    def format(self):
        return ""
    
    def is_allowed_data(self, key: str, value: str) -> tuple[bool, str]:
        try:
            number = int(value)
        except:
            return (False, f"The value {value} is not a number")
        if number < 0:
            return (False, f"The value {value} is negative")
        return (True, None)
    
    async def is_valid(self, dict: dict) -> tuple[bool, str]:
        return (True, None)
    
    async def callback(self, interaction: discord.Interaction):
        
        to_update = {}
        for child in self.children:
            
            allowed, error_message = self.is_allowed_data(child.key, child.value)
            if allowed:
                to_update[child.key] = int(child.value)
            else:
                embed = discord.Embed(title="Invalid input on form",
                        description=f"The value {child.value} is invalid for {child.label}. Reason: {error_message} ", color=0xFF0000)
                return await interaction.response.send_message(embeds=[embed], delete_after=15)
            
        valid, error_message = await self.is_valid(to_update)
        if valid:
            self.data.update(to_update)
        else:
            embed = discord.Embed(title="Invalid input on form",
                    description=f"Reason: {error_message} ", color=0xFF0000)
            return await interaction.response.send_message(embeds=[embed], delete_after=15)
        
        for child in self.children:
            child.value = str(self.data.get(child.key))

        embed = discord.Embed(
            title="The form submitted successfully",
            description=self.format(),
            colour=discord.Color.green(),
        )
        await interaction.response.send_message(embeds=[embed], ephemeral=True, delete_after=5)
        await self.update_co()

        
class DateModal(Modal):
    
    def __init__(self, update_co, database: Database, guild_id: int, now: datetime, data: dict) -> None:
        super().__init__(
            InputText(
                label="start year",
                placeholder="Put the year when your recurrent timed role will start",
                style=discord.InputTextStyle.singleline,
                required=True,
                value=f"{now.year}" if data is None else data.get("year"),
                key="year"
            ),
            InputText(
                label="start month",
                placeholder="Put the month when your recurrent timed role will start",
                style=discord.InputTextStyle.singleline,
                required=True,
                value=f"{now.month}" if data is None else data.get("month"),
                key="month"
            ),
            InputText(
                label="start day",
                placeholder="Put the day when your recurrent timed role will start",
                style=discord.InputTextStyle.singleline,
                value=f"{now.day}" if data is None else data.get("day"),
                required=True,
                key="day"
            ),
            title="Start date form", update_co=update_co, data=data
        )
        self.database = database
        self.guild_id = guild_id
        
    def format(self):
        year, month, day = self.data["year"], self.data["month"], self.data["day"]
        return f"New date set: {year}-{month}-{day}"
    
    async def is_valid(self, dict: dict) -> tuple[bool, str]:
        timezone = await self.database.get_timezone(self.guild_id)
        tz = None
        if timezone is not None:
            tz = pytz.timezone(timezone)
        now = datetime.now(tz=tz)
        input = datetime(year=dict["year"], month=dict["month"], day= dict["day"], tzinfo=tz)
        if now.strftime("%Y/%m/%d") > input.strftime("%Y/%m/%d"):
            return (False, f"The date input({input}) is in the past(now = {now})")
        return (True, None)
    
class TimeModal(Modal):
    def __init__(self, update_co, data: dict) -> None:
        super().__init__(
            InputText(
                label="start hour",
                placeholder="Put the hour when your recurrent timed role will start",
                style=discord.InputTextStyle.singleline,
                required=True,
                key="hours",
                value=None if data is None else str(data.get("hours"))
            ),
            InputText(
                label="start minute",
                placeholder="Put the minutes when your recurrent timed role will start",
                style=discord.InputTextStyle.singleline,
                required=True,
                key="minutes",
                value=None if data is None else str(data.get("minutes"))
            ),
            InputText(
                label="start second",
                placeholder="Put the seconds when your recurrent timed role will start",
                style=discord.InputTextStyle.singleline,
                required=True,
                key="seconds",
                value=None if data is None else str(data.get("seconds"))
            ),
            title="Start time form", update_co=update_co, data=data
        )

    def format(self):
        hours, minutes, seconds = self.data["hours"], self.data["minutes"], self.data["seconds"]
        time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        return f"New time set: {time}"

    async def is_valid(self, dict: dict) -> tuple[bool, str]:
        hours, minutes, seconds = int(dict["hours"]), int(dict["minutes"]), int(dict["seconds"])
        if hours > 23:
            return (False, f"The hour {hours} is greater then 23")
        if minutes > 59:
            return (False, f"The minute {hours} is greater then 59")
        if seconds > 59:
            return (False, f"The second {seconds} is greater then 59")
        return (True, None)
    
class DeltaModal(Modal):
    def __init__(self, update_co, data: dict) -> None:
        super().__init__(
            InputText(
                label="nb of days",
                placeholder="Put the nb of days before role reset",
                style=discord.InputTextStyle.singleline,
                required=True,
                key="days_delta",
                value=None if data is None else str(data.get("days_delta"))
            ),
            InputText(
                label="nb of hours",
                placeholder="Put the nb of hours before role reset",
                style=discord.InputTextStyle.singleline,
                required=True,
                key="hours_delta",
                value="0" if data is None else str(data.get("hours_delta"))
            ),
            InputText(
                label="nb of minutes",
                placeholder="Put the nb of minutes before role reset",
                style=discord.InputTextStyle.singleline,
                required=True,
                key="minutes_delta",
                value="0" if data is None else str(data.get("minutes_delta"))
            ),
            title="Time interval form", update_co=update_co, data=data)
        
    def format(self):
        days, hours, minutes = self.data["days_delta"], self.data["hours_delta"], self.data["minutes_delta"]
        time = timedelta(days=days, hours=hours, minutes=minutes)
        return f"New time interval set: {time}"
        
class ButtonCallModal(discord.ui.Button):
    
    def __init__(self, modal: discord.ui.Modal, label: str, style: discord.ButtonStyle, author_id: int):
        super().__init__(label=label, style=style, row=1)
        self.modal = modal
        self.author_id = author_id
        
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("Only the author of this command can use the buttons", ephemeral=True, delete_after=10)
        await interaction.response.send_modal(self.modal)
        
    def get_data(self) -> dict:
        return self.modal.data

        
class RecurrentRoleAddUpdateView(discord.ui.View):
    
    def __init__(self, guild_id: int, database: Database, role: Role, now: datetime, author_id: int,
             date_data: dict = None, time_data: dict = None, delta_data: dict = None):
        super().__init__(
            ButtonCallModal(
                DateModal(self.on_update, database, guild_id, now, date_data),
                label="Select start date", style=discord.ButtonStyle.primary, author_id=author_id
            ),
            ButtonCallModal(
                TimeModal(self.on_update, time_data),
                label="Select start time (default = 00h00:00s )" if time_data is None else "Select start time",
                style=discord.ButtonStyle.primary, author_id=author_id
            ),
            ButtonCallModal(
                DeltaModal(self.on_update, delta_data),
                label="Select time interval", style=discord.ButtonStyle.primary, author_id=author_id
            ),
            disable_on_timeout=True
        )
        self.is_editing = date_data is not None or time_data is not None or delta_data is not None
        if not self.is_editing:
            self.add_item(discord.ui.Button(label="Approve", style=discord.ButtonStyle.success, disabled=True, row=2))
            self.add_item(discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red, disabled=False, row=2))
            self.children[3].callback = self.approve_callback
            self.children[4].callback = self.cancel_callback
        self.interaction = None
        self.data = {}
        self.approved: bool = False
        self.guild_id: int = guild_id
        self.database: Database = database
        self.role: Role = role
        self.author_id: int = author_id
        self.is_editing = date_data is not None or time_data is not None or delta_data is not None
        
    def update_data(self):
        for child in self.children:
            if isinstance(child, ButtonCallModal):
                self.data.update(child.get_data())
                
    async def cancel_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("Only the author of this command can use the buttons", ephemeral=True)
        await interaction.response.send_message("Cancelled !", ephemeral=True)
        self.disable_all_items()
        embed = discord.Embed(title="Create a recurrent timed role",
                              description=f"cancelled")
        await self.interaction.edit_original_response(embed=embed, view=self)
        self.stop()
                
    async def approve_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("Only the author of this command can use the buttons", ephemeral=True)
        insert_info = await self.database.insert_or_update_recurring_time_role(self.role.id, self.guild_id,
            self.get_start_datetime(),
            self.get_deltatime()
        )
        self.approved = True

        timezone = await self.database.get_timezone(self.guild_id)
        if timezone is None:
            timezone = "(not set timezone)"
        embed = discord.Embed(
            title="Reccurent role added !",
            description=f"Starting at {insert_info[1]} in {timezone}, the role {self.role.mention} will be removed for all members each {insert_info[3]}. Next removal is at {insert_info[2]}"
        )
        await interaction.response.send_message(embeds=[embed], ephemeral=True)
        self.disable_all_items()
        await self.on_update()
        self.stop()
        
    def set_origin_interaction(self, interaction: discord.Interaction):
        self.interaction = interaction

    def get_from_data(self, key: str):
        result = self.data.get(key)
        if result is None:
            return 0
        return result

    def get_start_datetime(self) -> datetime:
        return datetime(
            year=self.get_from_data("year"), month=self.get_from_data("month"),
            day=self.get_from_data("day"), hour=self.get_from_data("hours"), minute=self.get_from_data("minutes"),
            second=self.get_from_data("seconds")
        )
    
    def get_deltatime(self) -> timedelta:
        delta =  timedelta(
            days=self.get_from_data("days_delta"),
            hours=self.get_from_data("hours_delta"),
            minutes=self.get_from_data("minutes_delta"),
        )
        if delta.total_seconds() == 0:
            return None
        return delta
        
    async def on_update(self):
        self.update_data()
        timezone = await self.database.get_timezone(self.guild_id)
        if timezone is None:
            timezone = "not set"
        year = self.data.get("year")
        month = self.data.get("month")
        day = self.data.get("day")
        hours = self.data.get("hours")
        minutes = self.data.get("minutes")
        seconds = self.data.get("seconds")
        days_delta = self.data.get("days_delta")
        hours_delta = self.data.get("hours_delta")
        minutes_delta = self.data.get("minutes_delta")
        
        current_date = None
        if year is not None and month is not None and day is not None:
            current_date = date(year=year, month=month, day=day)
        current_time = timedelta(seconds=0)
        if hours is not None and minutes is not None and seconds is not None:
            current_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        current_interval = None
        if days_delta is not None and hours_delta is not None and minutes_delta is not None:
            current_interval = timedelta(days=days_delta, hours=hours_delta, minutes=minutes_delta)
            
        if current_date is not None and current_time is not None and current_interval is not None and not self.approved and not self.is_editing:
            self.children[3].disabled = False
        
        if self.is_editing:
            start_datetime = self.get_start_datetime()
            delta = self.get_deltatime()
            _, next_datetime = await self.database.insert_or_update_recurring_time_role(self.role.id, self.guild_id, start_datetime, delta)
            embed = generate_edit_embed(self.role.mention, start_datetime, delta, timezone, next_datetime)
        else:
            embed = generate_insert_embed(self.role.mention, self.get_start_datetime(), self.get_deltatime(), timezone, approved=self.approved)      
        await self.interaction.edit_original_response(embed=embed, view=self)