import os
import discord
import aiohttp
import json

COC_API_TOKEN = os.getenv("API_TOKEN")
LINKED_PLAYERS_FILE = "linked_players.json"

async def get_coc_player(player_tag):
    url = f"https://cocproxy.royaleapi.dev/v1/players/{player_tag.replace('#', '%23')}"
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

def load_linked_players():
    try:
        with open(LINKED_PLAYERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_linked_players(data):
    with open(LINKED_PLAYERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def setup(bot):
    @bot.tree.command(name="linkaccount", description="Link your account to your Discord.")
    @discord.app_commands.describe(tag="e.g. #2Q82LRL")
    async def linkaccount_command(interaction: discord.Interaction, tag: str):
        await interaction.response.defer(ephemeral=True)
        player_tag = tag.upper().replace("O", "0")
        if not player_tag.startswith("#"):
            player_tag = "#" + player_tag

        player_data = await get_coc_player(player_tag)
        if not player_data:
            await interaction.followup.send("😓 Invalid player tag.",)
            return
        player_name = player_data.get("name", "?")

        data = load_linked_players()
        user_id = str(interaction.user.id)
        if user_id not in data:
            data[user_id] = []
        if any(acc['tag'].upper() == player_tag for acc in data[user_id]):
            await interaction.followup.send(f"Already has linked the account ({player_name}) `{player_tag}` to your Discord.",)
            return
        data[user_id].append({"name": player_name, "tag": player_tag})
        save_linked_players(data)
        await interaction.followup.send(f"✅ Successfully linked account `{player_name}` ({player_tag}) to your Discord.", )