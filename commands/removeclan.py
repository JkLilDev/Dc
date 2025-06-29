import discord
import json
import os

LINKED_CLANS_FILE = "linked_clans.json"

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
    @bot.tree.command(name="removeclan", description="Remove a clan linked to this server.")
    async def removeclan_command(interaction: discord.Interaction):
        # Admin check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("😓 You don't have admin permission to use this command.", ephemeral=True)
            return

        data = load_linked_clans()
        guild_id = str(interaction.guild.id)
        clans = data.get(guild_id, [])
        if not clans:
            await interaction.response.send_message(
                "No clans are linked to this server.", ephemeral=True
            )
            return

        options = [
            discord.SelectOption(label=f"{clan['name']} ({clan['tag']})", value=clan['tag'])
            for clan in clans
        ]

        class RemoveClanSelect(discord.ui.View):
            @discord.ui.select(placeholder="Select a clan to remove...", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: discord.ui.Select):
                tag_to_remove = select.values[0]
                data2 = load_linked_clans()
                new_clans = [c for c in data2[guild_id] if c['tag'] != tag_to_remove]
                data2[guild_id] = new_clans
                save_linked_clans(data2)
                await select_interaction.response.edit_message(
                    content=f"✅ Removed clan with tag `{tag_to_remove}`.",
                    view=None
                )

        await interaction.response.send_message(
            "Select the clan you want to remove:",
            view=RemoveClanSelect(),
            ephemeral=True
        )