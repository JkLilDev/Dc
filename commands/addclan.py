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

def save_linked_clans(data):
    with open(LINKED_CLANS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def setup(bot):
    @bot.tree.command(name="addclan", description="Link a clan to this server.")
    @discord.app_commands.describe(tag="e.g. #2Q82LRL")
    async def addclan_command(interaction: discord.Interaction, tag: str):
        # Admin check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("😓 You don't have admin permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        clan_tag = tag.upper().replace("O", "0")
        if not clan_tag.startswith("#"):
            clan_tag = "#" + clan_tag

        clan_data = await get_coc_clan(clan_tag)
        if not clan_data:
            await interaction.followup.send("😓 Invalid clan tag",)
            return
        clan_name = clan_data.get("name", "?")

        data = load_linked_clans()
        guild_id = str(interaction.guild.id)
        if guild_id not in data:
            data[guild_id] = []
        if any(acc['tag'].upper() == clan_tag for acc in data[guild_id]):
            await interaction.followup.send(
                f"Already has linked the clan ({clan_name}) `{clan_tag}` to this server.",)
            return
        data[guild_id].append({"name": clan_name, "tag": clan_tag})
        save_linked_clans(data)
        await interaction.followup.send(
            f"✅ Successfully linked clan ({clan_name}) `{clan_tag}` to this server.",)