import os
import discord
import aiohttp
import json

COC_API_TOKEN = os.getenv("API_TOKEN")
LINKED_PLAYERS_FILE = "linked_players.json"

class PlayerEmbeds:
    ELIXIR_TROOPS = [
        "Barbarian", "Archer", "Giant", "Goblin", "Wall Breaker", "Balloon", "Wizard",
        "Healer", "Dragon", "P.E.K.K.A", "Baby Dragon", "Miner", "Electro Dragon", "Yeti", "Dragon Rider",
        "Electro Titan", "Root Rider", "Thrower"
    ]
    DARK_TROOPS = [
        "Minion", "Hog Rider", "Valkyrie", "Golem", "Witch", "Lava Hound", "Bowler",
        "Ice Golem", "Headhunter", "Apprentice Warden", "Druid", "Furnace"
    ]
    SUPER_TROOPS = [
        "Super Barbarian", "Super Archer", "Super Giant", "Sneaky Goblin", "Super Wall Breaker",
        "Rocket Balloon", "Super Wizard", "Super Dragon", "Inferno Dragon", "Super Miner", "Super Yeti",
        "Super Minion", "Super Hog Rider", "Super Valkyrie", "Super Witch", "Ice Hound", "Super Bowler"
    ]
    PETS = [
        "L.A.S.S.I", "Electro Owl", "Mighty Yak", "Unicorn", "Frosty", "Diggy", "Poison Lizard",
        "Phoenix", "Spirit Fox", "Angry Jelly", "Sneezy"
    ]
    ELIXIR_SPELLS = [
        "Lightning Spell", "Healing Spell", "Rage Spell", "Jump Spell", "Freeze Spell", "Clone Spell",
        "Invisibility Spell", "Recall Spell", "Revive Spell"
    ]
    DARK_SPELLS = [
        "Poison Spell", "Earthquake Spell", "Haste Spell", "Skeleton Spell", "Bat Spell",
        "Overgrowth Spell", "Ice Block Spell"
    ]
    SIEGE_MACHINES = [
        "Wall Wrecker", "Battle Blimp", "Stone Slammer", "Siege Barracks", "Log Launcher",
        "Flame Flinger", "Battle Drill", "Troop Launcher"
    ]
    HERO_EQUIPMENT_NAMES = [
        "Giant Gauntlet", "Rocket Spear", "Spiky Ball", "Frozen Arrow", "Fireball",
        "Snake Bracelet", "Dark Crown", "Magic Mirror", "Electro Boots", "Action Figure",
        "Barbarian Puppet", "Rage Vial", "Archer Puppet", "Invisibility Vial", "Eternal Tome",
        "Life Gem", "Seeking Shield", "Royal Gem", "Earthquake Boots", "Hog Rider Puppet",
        "Haste Vial", "Giant Arrow", "Healer Puppet", "Rage Gem", "Healing Tome",
        "Henchmen Puppet", "Dark Orb", "Metal Pants", "Vampstache", "Noble Iron"
    ]

    @staticmethod
    def player_info(player_data):
        embed = discord.Embed(
            title=f"{player_data.get('name', '?')} ({player_data.get('tag', '?')})",
            color=discord.Color.green()
        )
        embed.add_field(name="Town Hall", value=player_data.get("townHallLevel", "?"))
        embed.add_field(name="Exp Level", value=player_data.get("expLevel", "?"))
        embed.add_field(name="Trophies", value=player_data.get("trophies", "?"))
        embed.add_field(name="Clan", value=player_data.get("clan", {}).get("name", "None"))
        league = player_data.get("league", {}).get("name")
        if league:
            embed.add_field(name="League", value=league)
        icon = player_data.get("league", {}).get("iconUrls", {}).get("medium")
        if icon:
            embed.set_thumbnail(url=icon)
        embed.set_footer(text="Click 'Unit' button for more information.")
        return embed

    @staticmethod
    def unit_embed(player_data):
        troops = player_data.get("troops", [])
        spells = player_data.get("spells", [])
        heroes = player_data.get("heroes", [])
        hero_equipment = player_data.get("heroEquipment", [])

        def troop_lines(names):
            return "\n".join(
                f"{t['name']}: {t['level']}/{t['maxLevel']}" for t in troops if t.get("name") in names
            ) or "None"

        def spell_lines(names):
            return "\n".join(
                f"{s['name']}: {s['level']}/{s['maxLevel']}" for s in spells if s.get("name") in names
            ) or "None"

        def pet_lines():
            return "\n".join(
                f"{t['name']}: {t['level']}/{t['maxLevel']}" for t in troops if t.get("name") in PlayerEmbeds.PETS
            ) or "None"

        def siege_lines():
            return "\n".join(
                f"{t['name']}: {t['level']}/{t['maxLevel']}" for t in troops if t.get("name") in PlayerEmbeds.SIEGE_MACHINES
            ) or "None"

        def hero_lines():
            return "\n".join(
                f"{h['name']}: {h['level']}/{h['maxLevel']}" for h in heroes
            ) or "None"

        def equipment_lines():
            if hero_equipment:
                result = "\n".join(
                    f"{eq['name']}: {eq.get('level', '?')}/{eq.get('maxLevel', '?')}"
                    for eq in hero_equipment if eq.get("name") in PlayerEmbeds.HERO_EQUIPMENT_NAMES
                )
                if result:
                    return result
            return "None"

        embed = discord.Embed(
            title="Army Overview",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Elixir Troops", value=troop_lines(PlayerEmbeds.ELIXIR_TROOPS), inline=False)
        embed.add_field(name="Dark Troops", value=troop_lines(PlayerEmbeds.DARK_TROOPS), inline=False)
        embed.add_field(name="Super Troops", value=troop_lines(PlayerEmbeds.SUPER_TROOPS), inline=False)
        embed.add_field(name="Elixir Spells", value=spell_lines(PlayerEmbeds.ELIXIR_SPELLS), inline=False)
        embed.add_field(name="Dark Spells", value=spell_lines(PlayerEmbeds.DARK_SPELLS), inline=False)
        embed.add_field(name="Siege Machines", value=siege_lines(), inline=False)
        embed.add_field(name="Pets", value=pet_lines(), inline=False)
        embed.add_field(name="Heroes", value=hero_lines(), inline=False)
        embed.add_field(name="Hero Equipment", value=equipment_lines(), inline=False)
        embed.set_footer(text="Click 'Back' to return to profile.")
        return embed

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

class ProfileButtonView(discord.ui.View):
    def __init__(self, player_data, show_unit=False):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.show_unit = show_unit

        # Toggle button
        label = "Back" if self.show_unit else "Unit"
        self.unit_btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id="unit_btn")
        self.unit_btn.callback = self.unit_btn_callback
        self.add_item(self.unit_btn)

        # Open In-game link button
        tag = player_data.get("tag", "").replace("#", "")
        if tag:
            url = f"https://link.clashofclans.com/?action=OpenPlayerProfile&tag=%23{tag}"
            self.add_item(discord.ui.Button(label="Open In-game", url=url, style=discord.ButtonStyle.link))

    async def unit_btn_callback(self, interaction: discord.Interaction):
        self.show_unit = not self.show_unit
        new_view = ProfileButtonView(self.player_data, show_unit=self.show_unit)
        if self.show_unit:
            embed = PlayerEmbeds.unit_embed(self.player_data)
        else:
            embed = PlayerEmbeds.player_info(self.player_data)
        await interaction.response.edit_message(embed=embed, view=new_view)

def setup(bot):
    async def player_tag_autocomplete(interaction: discord.Interaction, current: str):
        data = load_linked_players()
        user_id = str(interaction.user.id)
        accounts = data.get(user_id, [])
        return [
            discord.app_commands.Choice(
                name=f"{acc['name']} ({acc['tag']})",
                value=acc['tag']
            )
            for acc in accounts
            if current.lower() in acc['tag'].lower() or current.lower() in acc['name'].lower()
        ][:25]

    @bot.tree.command(name="player", description="Get player information")
    @discord.app_commands.describe(tag="e.g. #2Q82LRL")
    @discord.app_commands.autocomplete(tag=player_tag_autocomplete)
    async def player_command(interaction: discord.Interaction, tag: str):
        await interaction.response.defer()
        player_data = await get_coc_player(tag)
        if not player_data:
            await interaction.followup.send("😓 Invalid player tag.",)
            return

        view = ProfileButtonView(player_data, show_unit=False)
        embed = PlayerEmbeds.player_info(player_data)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)