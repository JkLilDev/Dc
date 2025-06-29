import discord
import os

def setup(bot):
    @bot.tree.command(name="help", description="Get bot command details")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            description=(
                "## ClashBerry Commands\n\n"
                "**/clan**\nGet info about a clan.\n\n"
                "**/player**\nGet info about a playe.\n\n"
                "**/addclan**\nLink a clan to this server.\n\n"
                "**/linkaccount**\nLink your account to your Discord.\n\n"
                "**/war**\nShow current war info for a clan.\n\n"
                "**/removeclan**\nRemove a clan linked to this server.\n\n"
                "**/setup_ticket**\nSetup the clan application ticket panel.\n\n"
                "**/unlinkaccount**\nUnlink one of your linked accounts."
            ),
            color=discord.Color.blurple()
        )

        embed.set_image(url="attachment://file.jpg")
        embed.set_footer(text="If you need more help or facing any error or have any suggestions join our support server to report.")

        class SupportButton(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(
                    discord.ui.Button(
                        label="Support Server",
                        url="https://discord.gg/WVvqR7ysBZ",
                        style=discord.ButtonStyle.link
                    )
                )

        image_path = os.path.join(os.path.dirname(__file__), "file.jpg")
        file = discord.File(image_path, filename="file.jpg")

        await interaction.response.send_message(
            embed=embed,
            view=SupportButton(),
            file=file
        )
