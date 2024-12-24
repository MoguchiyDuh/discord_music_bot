import discord
from discord.ext import commands
from discord import app_commands


class TempChannelsGroup(app_commands.Group):
    """Cog for managing temporary voice channels."""

    def __init__(self, bot: commands.Bot):
        super().__init__(name="temp-channels", description="Manage temporary channels.")
        self.temp_channels = (
            {}
        )  # {channel_id: {"owner": user_id, "guild_id": guild_id}}

    async def __get_category(self, guild: discord.Guild) -> discord.CategoryChannel:
        """Get or create the 'TEMP CHANNELS' category."""
        category = discord.utils.get(guild.categories, name="TEMP CHANNELS")
        if category is None:
            category = await guild.create_category("TEMP CHANNELS")
        return category

    async def __create_temp_channel(
        self, member: discord.Member, category: discord.CategoryChannel
    ) -> discord.VoiceChannel:
        """Create a temporary voice channel for the member."""
        channel_name = f"{member.display_name}'s Channel"
        temp_channel = await category.create_voice_channel(
            name=channel_name, user_limit=0
        )
        await member.move_to(temp_channel)
        self.temp_channels[temp_channel.id] = {
            "owner": member.id,
            "guild_id": member.guild.id,
        }
        return temp_channel

    async def __delete_temp_channel(self, channel: discord.VoiceChannel):
        """Delete a temporary channel if it's empty."""
        if len(channel.members) == 0:
            await channel.delete()
            del self.temp_channels[channel.id]
            print(f"Deleted empty temp channel {channel.name}")

    async def __get_user_temp_channel(
        self, interaction: discord.Interaction
    ) -> discord.VoiceChannel | None:
        """Get the user's temporary channel."""
        for channel_id, info in self.temp_channels.items():
            if (
                info["owner"] == interaction.user.id
                and info["guild_id"] == interaction.guild.id
            ):
                return interaction.guild.get_channel(channel_id)
        return None

    @commands.Cog.listener()
    async def on_ready(self):
        """Ensure the 'TEMP CHANNELS' category and lobby channel exist."""
        for guild in self.bot.guilds:
            category = await self.__get_category(guild)
            if not discord.utils.get(category.voice_channels, name="Join to create"):
                await category.create_voice_channel("Join to create")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Create and delete temp channels on user voice state updates."""
        if before.channel == after.channel:  # No change in channel
            return

        # 'Join to Create' logic
        if after.channel and after.channel.name.lower() == "join to create":
            category = await self.__get_category(member.guild)
            await self.__create_temp_channel(member, category)

        if before.channel and before.channel.id in self.temp_channels:
            await self.__delete_temp_channel(before.channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Cleanup when a temp channel is deleted manually."""
        if channel.id in self.temp_channels:
            del self.temp_channels[channel.id]

    async def __update_channel_permissions(
        self,
        temp_channel: discord.VoiceChannel,
        interaction: discord.Interaction,
        allow: bool,
    ):
        """Helper function to lock/unlock the channel."""
        await temp_channel.set_permissions(
            interaction.guild.default_role, connect=allow
        )
        action = "locked" if not allow else "unlocked"
        return f"Your channel has been {action}."

    @app_commands.command(name="lock", description="Lock your temporary channel.")
    async def lock(self, interaction: discord.Interaction):
        """Lock the user's temporary channel."""
        temp_channel = await self.__get_user_temp_channel(interaction)
        if temp_channel:
            message = await self.__update_channel_permissions(
                temp_channel, interaction, False
            )
            await interaction.response.send_message(message)
        else:
            await interaction.response.send_message(
                "You don't own a temporary channel.", ephemeral=True
            )

    @app_commands.command(name="unlock", description="Unlock your temporary channel.")
    async def unlock(self, interaction: discord.Interaction):
        """Unlock the user's temporary channel."""
        temp_channel = await self.__get_user_temp_channel(interaction)
        if temp_channel:
            message = await self.__update_channel_permissions(
                temp_channel, interaction, True
            )
            await interaction.response.send_message(message)
        else:
            await interaction.response.send_message(
                "You don't own a temporary channel.", ephemeral=True
            )

    @app_commands.command(name="rename", description="Rename your temporary channel.")
    async def rename(self, interaction: discord.Interaction, name: str):
        """Rename the user's temporary channel."""
        temp_channel = await self.__get_user_temp_channel(interaction)
        if temp_channel:
            await temp_channel.edit(name=name)
            await interaction.response.send_message(
                f"Your channel has been renamed to: {name}."
            )
        else:
            await interaction.response.send_message(
                "You don't own a temporary channel.", ephemeral=True
            )

    @app_commands.command(
        name="limit", description="Set a user limit for your temporary channel."
    )
    async def limit(self, interaction: discord.Interaction, limit: int):
        """Set the user limit for the user's temporary channel."""
        temp_channel = await self.__get_user_temp_channel(interaction)
        if temp_channel:
            await temp_channel.edit(user_limit=limit)
            await interaction.response.send_message(f"User limit set to: {limit}.")
        else:
            await interaction.response.send_message(
                "You don't own a temporary channel.", ephemeral=True
            )

    @app_commands.command(
        name="kick", description="Kick a user from your temporary channel."
    )
    async def kick(self, interaction: discord.Interaction, member: discord.Member):
        """Kick a member from the user's temporary channel."""
        temp_channel = await self.__get_user_temp_channel(interaction)
        if temp_channel and member.voice and member.voice.channel == temp_channel:
            await member.move_to(None)  # Disconnect the user
            await interaction.response.send_message(
                f"{member.display_name} has been kicked from your channel."
            )
        else:
            await interaction.response.send_message(
                "The user is not in your channel or you don't own a temporary channel.",
                ephemeral=True,
            )


class TempChannels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(TempChannelsGroup(bot))


async def setup(bot: commands.Bot):
    """Setup function to load the cog."""
    await bot.add_cog(TempChannels(bot))
