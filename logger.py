import discord

LOG_CHANNEL_ID = 1387165662975103139  

async def log_guild_join(bot: discord.Client, guild: discord.Guild):
    """Logs when the bot joins a new server."""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if log_channel:
        # Fetch the user who added the bot from audit logs
        added_by = "Unknown"
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.bot_add):
            if entry.target.id == bot.user.id:
                added_by = entry.user.mention
                break

        # Build embed
        embed = discord.Embed(
            title=f"🍓 Added to {guild.name}",
            description=(
                f"ClashBerry bot added to new server **{guild.name}**.\n\n"
                f"Server ID: `{guild.id}`\n\n"
                f"Added by {added_by}"
                
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Now in Total {len(bot.guilds)} servers.")

        # Set thumbnail to server icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await log_channel.send(embed=embed)