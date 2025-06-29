import discord
import json
import os

LINKED_PLAYERS_FILE = "linked_players.json"

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
    @bot.tree.command(name="unlinkaccount", description="Unlink one of your accounts.")
    async def unlinkaccount_command(interaction: discord.Interaction):
        data = load_linked_players()
        user_id = str(interaction.user.id)
        accounts = data.get(user_id, [])
        if not accounts:
            await interaction.response.send_message("You have no linked accounts to unlink.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=f"{acc['name']} ({acc['tag']})", value=acc['tag'])
            for acc in accounts
        ]

        class UnlinkSelect(discord.ui.View):
            @discord.ui.select(placeholder="Select an account to unlink...", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: discord.ui.Select):
                tag_to_remove = select.values[0]
                data2 = load_linked_players()
                new_accounts = [a for a in data2[user_id] if a['tag'] != tag_to_remove]
                data2[user_id] = new_accounts
                save_linked_players(data2)
                await select_interaction.response.edit_message(
                    content=f"✅ Unlinked account with tag `{tag_to_remove}`.",
                    view=None
                )

        await interaction.response.send_message(
            "Select the account you want to unlink:",
            view=UnlinkSelect(),
            ephemeral=True
        )