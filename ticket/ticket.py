import os
import json
import discord
import aiohttp

COC_API_TOKEN = os.getenv("API_TOKEN")
STAFF_ROLES_FILE = "staff_roles.json"
staff_roles = {}

def load_staff_roles():
    global staff_roles
    try:
        with open(STAFF_ROLES_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                staff_roles = data
            else:
                staff_roles = {}
    except (FileNotFoundError, json.JSONDecodeError):
        staff_roles = {}

def save_staff_roles():
    with open(STAFF_ROLES_FILE, "w") as f:
        json.dump(staff_roles, f, indent=2)

def get_staff_role(guild):
    staff_obj = staff_roles.get(str(guild.id))
    if staff_obj and isinstance(staff_obj, dict):
        staff_role_id = staff_obj.get("staff_role")
        if staff_role_id:
            role = guild.get_role(staff_role_id)
            return role
    return None

def get_category_id(guild):
    staff_obj = staff_roles.get(str(guild.id))
    if staff_obj and isinstance(staff_obj, dict):
        return staff_obj.get("category_id")
    return None

load_staff_roles()

async def get_coc_player(player_tag):
    url = f"https://cocproxy.royaleapi.dev/v1/players/{player_tag.replace('#', '%23')}"
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return None

async def show_profile(interaction, player_data):
    th_level = player_data.get("townHallLevel", "?")
    name = player_data.get("name", "?")
    tag = player_data.get("tag", "?")
    exp_level = player_data.get("expLevel", "?")
    trophies = player_data.get("trophies", "?")
    clan = player_data.get("clan", {}).get("name", "None")
    embed = discord.Embed(
        title=f"{name} ({tag})",
        color=discord.Color.green(),
        description=(
            f"TH Level: **{th_level}**\n"
            f"Exp Level: **{exp_level}**\n"
            f"Trophies: **{trophies}**\n"
            f"Clan: **{clan}**"
        )
    )
    if "league" in player_data and "iconUrls" in player_data["league"]:
        icon = player_data["league"]["iconUrls"].get("medium")
        if icon:
            embed.set_thumbnail(url=icon)
    await interaction.response.send_message(embed=embed, ephemeral=True)

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply now", style=discord.ButtonStyle.success, custom_id="apply_now")
    async def apply_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        normalized_username = interaction.user.name.lower().replace('.', '')
        channel_name = f"ticket-{normalized_username}"
        found_channel = None
        for channel in interaction.guild.text_channels:
            if channel.name == channel_name:
                found_channel = channel
                break
        if found_channel:
            embed = discord.Embed(
                description=f"You have already opened a ticket: {found_channel.mention}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        staff_role = get_staff_role(interaction.guild)
        staff_role_id = staff_role.id if staff_role else None
        await interaction.response.send_modal(TagModal(staff_role_id, normalized_username))

class TagModal(discord.ui.Modal, title="Enter In-game Tag"):
    tag = discord.ui.TextInput(
        label="Player Tag",
        placeholder="e.g. #2Q82LRL",
        required=True,
        min_length=5,
        max_length=15
    )

    def __init__(self, staff_role_id, username):
        super().__init__()
        self.staff_role_id = staff_role_id
        self.username = username

    async def on_submit(self, interaction: discord.Interaction):
        player_tag = self.tag.value.replace(" ", "").upper().replace("O", "0")
        if not player_tag.startswith("#"):
            player_tag = "#" + player_tag

        await interaction.response.defer(ephemeral=True, thinking=True)
        player_data = await get_coc_player(player_tag)
        if player_data is None:
            await interaction.followup.send("😓 Invalid player tag.", ephemeral=True)
            return

        name = player_data.get("name", "?")
        tag = player_data.get("tag", "?")

        embed = discord.Embed(
            title="{name} ({tag})",
            description=(
                f"Please confirm if you're applying with this account."
            ),
            color=discord.Color.yellow()
        )
        await interaction.followup.send(
            embed=embed,
            view=ConfirmAccountView(player_data, self.staff_role_id, self.username),        ephemeral=True
        )

class ConfirmAccountView(discord.ui.View):
    def __init__(self, player_data, staff_role_id, username):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.staff_role_id = staff_role_id
        self.username = username

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, custom_id="confirm_account")
    async def confirm_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        channel_name = f"ticket-{user.name.lower()}"
        found_channel = None
        for channel in guild.text_channels:
            if channel.name == channel_name:
                found_channel = channel
                break

        staff_role = get_staff_role(guild)
        if not staff_role:
            await interaction.response.send_message("Staff role is not set up correctly for this server. Please run the /setup_ticket command again.", ephemeral=True)
            return

        if found_channel:
            embed = discord.Embed(
                description=f"You already have a ticket: {found_channel.mention}",
                color=discord.Color.red()
            )
            try:
                await interaction.response.edit_message(embed=embed, content=None, view=None)
            except discord.errors.NotFound:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return

        category_id = get_category_id(guild)
        category = guild.get_channel(category_id) if category_id else None

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            reason="Clan application ticket"
        )

        staff_mention = staff_role.mention if staff_role else "@Staff"
        embed = discord.Embed(
            title="Clan Application",
            description=(
                f"Welcome! to the clan application.\n\n"
                f"Your ticket will be handle shortly."
            ),
            color=discord.Color.green()
        )
        ticket_message = await ticket_channel.send(
            content=f"{user.mention} {staff_mention}",
            embed=embed,
            view=TicketActionsView(user.name.lower(), staff_role.id if staff_role else None, self.player_data)
        )
        await ticket_message.pin()

        confirm_embed = discord.Embed(
            title="✅ Ticket Created",
            description=f"Your ticket has been created: {ticket_channel.mention}",
            color=discord.Color.green()
        )
        self.children[0].disabled = True
        try:
            await interaction.response.edit_message(embed=confirm_embed, content=None, view=self)
        except discord.errors.NotFound:
            await interaction.followup.send(embed=confirm_embed, ephemeral=True)

class TicketActionsView(discord.ui.View):
    def __init__(self, username, staff_role_id, player_data):
        super().__init__(timeout=None)
        self.username = username
        self.staff_role_id = staff_role_id
        self.player_data = player_data

    @discord.ui.button(label="Player Account", style=discord.ButtonStyle.primary, custom_id="profile_button")
    async def profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.name.lower() != self.username:
            await interaction.response.send_message("Only the ticket creator can view the profile.", ephemeral=True)
            return
        await show_profile(interaction, self.player_data)

    @discord.ui.button(label="Delete Ticket", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = get_staff_role(interaction.guild)
        if not staff_role:
            await interaction.response.send_message("Staff role is not set up. Please run the /setup_ticket command again.", ephemeral=True)
            return
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("Please ask staff to delete this ticket.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Delete Confirmation",
            description="Are you sure you want to delete this ticket?",
            color=discord.Color.red()
        )
        await interaction.response.send_message(
            embed=embed,
            view=DeleteConfirmView(),
            ephemeral=True
        )

class DeleteConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class PanelEditModal(discord.ui.Modal, title="Setup Ticket Panel Embed"):
    title_in = discord.ui.TextInput(label="Embed Title", required=True, max_length=256)
    desc_in = discord.ui.TextInput(label="Embed Description", style=discord.TextStyle.paragraph, required=True, max_length=1024)
    img_in = discord.ui.TextInput(label="Image URL (optional)", required=False, max_length=300)

    def __init__(self, staff_role_id, preview_channel, category_id, message_id=None, channel_id=None):
        super().__init__()
        self.staff_role_id = staff_role_id
        self.preview_channel = preview_channel
        self.category_id = category_id
        self.message_id = message_id
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.title_in.value,
            description=self.desc_in.value,
            color=discord.Color.blurple()
        )
        if self.img_in.value:
            embed.set_image(url=self.img_in.value)

        if self.message_id and self.channel_id:
            channel = interaction.client.get_channel(self.channel_id)
            if channel:
                try:
                    msg = await channel.fetch_message(self.message_id)
                    await msg.edit(
                        embed=embed,
                        view=PreviewPanelSendOnlyView(self.staff_role_id, embed, self.preview_channel, self.category_id, msg.id, channel.id)
                    )
                    await interaction.response.defer()
                    return
                except discord.errors.NotFound:
                    pass
        await interaction.response.send_message(
            embed=embed,
            view=PreviewPanelSendOnlyView(self.staff_role_id, embed, self.preview_channel, self.category_id, None, None),
            ephemeral=True
        )

class PreviewPanelEditOnlyView(discord.ui.View):
    def __init__(self, staff_role_id, preview_embed, preview_channel, category_id, message_id, channel_id):
        super().__init__(timeout=60)
        self.staff_role_id = staff_role_id
        self.preview_embed = preview_embed
        self.preview_channel = preview_channel
        self.category_id = category_id
        self.message_id = message_id
        self.channel_id = channel_id

    @discord.ui.button(label="Setup Embed", style=discord.ButtonStyle.secondary)
    async def edit_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PanelEditModal(
            self.staff_role_id,
            self.preview_channel,
            self.category_id,
            message_id=self.message_id or (interaction.message.id if interaction.message else None),
            channel_id=self.channel_id or (interaction.channel.id if interaction.channel else None)
        ))

class PreviewPanelSendOnlyView(discord.ui.View):
    def __init__(self, staff_role_id, preview_embed, preview_channel, category_id, message_id, channel_id):
        super().__init__(timeout=60)
        self.staff_role_id = staff_role_id
        self.preview_embed = preview_embed
        self.preview_channel = preview_channel
        self.category_id = category_id
        self.message_id = message_id
        self.channel_id = channel_id

    @discord.ui.button(label="Send Panel", style=discord.ButtonStyle.success)
    async def save_and_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_channel = self.preview_channel or interaction.channel
        await target_channel.send(embed=self.preview_embed, view=TicketPanelView())
        button.disabled = True
        await interaction.response.edit_message(
            embed=self.preview_embed,
            view=self
        )
        self.stop()

def setup(bot):
    @bot.tree.command(
        name="setup_ticket",
        description="Setup the clan application ticket panel"
    )
    @discord.app_commands.describe(
        staff_role="Select role for staff",
        channel="Channel to send the ticket panel (optional)",
        category="Category for ticket channels (optional)"
    )
    async def setup_ticket_command(
        interaction: discord.Interaction,
        staff_role: discord.Role,
        channel: discord.TextChannel = None,
        category: discord.CategoryChannel = None
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)
        staff_roles[str(interaction.guild.id)] = {
            "staff_role": staff_role.id,
            "category_id": category.id if category else None
        }
        try:
            save_staff_roles()
        except Exception as e:
            print(f"Error saving staff_roles: {e}")

        preview_embed = discord.Embed(
            title="Ticket Panel Title",
            description="Ticket Panel Discription.\n\nSetup your panel embed using below button",
            color=discord.Color.blurple()
        )
        msg = await interaction.followup.send(
            embed=preview_embed,
            view=PreviewPanelEditOnlyView(staff_role.id, preview_embed, channel, category.id if category else None, None, None),
            ephemeral=True
        )
        view = PreviewPanelEditOnlyView(staff_role.id, preview_embed, channel, category.id if category else None, msg.id, msg.channel.id)
        await msg.edit(view=view)
  
