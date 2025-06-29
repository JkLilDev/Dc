import os
import discord
import aiohttp
import json

COC_API_TOKEN = os.getenv("API_TOKEN")
LINKED_CLANS_FILE = "linked_clans.json"

async def get_coc_clan_war(clan_tag):
    url = f"https://cocproxy.royaleapi.dev/v1/clans/{clan_tag.replace('#', '%23')}/currentwar"
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

    @bot.tree.command(name="war", description="Get clan war information.")
    @discord.app_commands.describe(tag="e.g. #2Q82LRL")
    @discord.app_commands.autocomplete(tag=clan_tag_autocomplete)
    async def war_command(interaction: discord.Interaction, tag: str):
        await interaction.response.defer()
        war_data = await get_coc_clan_war(tag)
        if not war_data or war_data.get("state") == "notInWar":
            await interaction.followup.send("😓 No current war found for this clan.")
            return

        clan = war_data.get("clan", {})
        opponent = war_data.get("opponent", {})
        embed = discord.Embed(
            title=f"War: {clan.get('name', '?')} vs {opponent.get('name', '?')}",
            color=discord.Color.red(),
        )
        embed.add_field(name="Our Stars", value=clan.get("stars", "?"))
        embed.add_field(name="Our Attacks", value=clan.get("attacks", 0))
        embed.add_field(name="Our Destruction", value=f"{clan.get('destructionPercentage', 0)}%")
        embed.add_field(name="Opponent Stars", value=opponent.get("stars", "?"))
        embed.add_field(name="Opponent Attacks", value=opponent.get("attacks", 0))
        embed.add_field(name="Opponent Destruction", value=f"{opponent.get('destructionPercentage', 0)}%")
        embed.add_field(name="State", value=war_data.get("state", "?"))
        embed.add_field(name="Team Size", value=war_data.get("teamSize", "?"))
        await interaction.followup.send(embed=embed)