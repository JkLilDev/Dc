import os
import discord
import aiohttp
import json

COC_API_TOKEN = os.getenv("API_TOKEN")
LINKED_CLANS_FILE = "linked_clans.json"

async def get_coc_clan(clan_tag):
    url = f"https://cocproxy.royaleapi.dev/v1/clans/{clan_tag.replace('#', '%23')}"
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

def load_linked_clans():
    try:
        with open(LINKED_CLANS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def setup(bot):
    async def clan_tag_autocomplete(interaction: discord.Interaction, current: str):
        data = load_linked_clans()
        guild_id = str(interaction.guild.id)
        clans = data.get(guild_id, [])
        return [
            discord.app_commands.Choice(
                name=f"{clan['name']} ({clan['tag']})",
                value=clan['tag']
            )
            for clan in clans
            if current.lower() in clan['tag'].lower() or current.lower() in clan['name'].lower()
        ][:25]

    @bot.tree.command(name="clan", description="Get clan information.")
    @discord.app_commands.describe(tag="e.g. #2Q82LRL")
    @discord.app_commands.autocomplete(tag=clan_tag_autocomplete)
    async def clan_command(interaction: discord.Interaction, tag: str):
        await interaction.response.defer()
        clan_data = await get_coc_clan(tag)
        if not clan_data:
            await interaction.followup.send("😓 Invalid clan tag.")
            return

        embed = discord.Embed(
            title=f"{clan_data.get('name', '?')} ({clan_data.get('tag', '?')})",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Level", value=clan_data.get("clanLevel", "?"))
        embed.add_field(name="Members", value=clan_data.get("members", "?"))
        embed.add_field(name="Type", value=clan_data.get("type", "?"))
        embed.add_field(name="Points", value=clan_data.get("clanPoints", "?"))
        embed.add_field(name="War Wins", value=clan_data.get("warWins", "?"))
        embed.add_field(name="Location", value=clan_data.get("location", {}).get("name", "None"))
        if clan_data.get("badgeUrls", {}).get("large"):
            embed.set_thumbnail(url=clan_data["badgeUrls"]["large"])
        await interaction.followup.send(embed=embed)