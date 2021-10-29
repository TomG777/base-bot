import discord
import requests
import urllib

from cmds import cmd
from events import event, channel_event


def get_user(config, user_id: str) -> dict:
    return requests.get(url="https://api.morningstreams.com/api/users/" + user_id,
                        headers={"Authorization": config.get("token")}).json()


def get_discord(config, user_id: str) -> dict:
    return requests.get(url="https://api.morningstreams.com/api/users/" + user_id + "/discord",
                        headers={"Authorization": config.get("token")}).json()


@cmd("getuserraw", __name__, help="Get raw info about user id", usage="<id>", hidden=True, mod=True)
async def command_getuserraw(text: str, config: dict, **_):
    return get_user(config, text)


@cmd("getuser", __name__, help="Get info about a user by their site id", usage="<id>")
async def command_getuser(text: str, config: dict, **_):
    user = get_user(config, text)
    if "nouserfound" in user.keys():
        return discord.Embed(title="User not found", description="ID `" + text + "` not found")
    else:
        embed = discord.Embed(title="Info about user")
        embed.add_field(name="id", value=user.get("id"))
        embed.add_field(name="username", value=user.get("username"))
        embed.add_field(name="stylised username", value=user.get("showUsername"))
        return embed


@cmd("getdiscord", __name__, help="Get info about a user by their site id", usage="<id>")
async def command_getuser(text: str, config: dict, **_):
    user = get_discord(config, text)
    if "nouserfound" in user.keys():
        return discord.Embed(title="User not found", description="ID `" + text + "` not found")
    else:
        embed = discord.Embed(title="Info about user")
        for k, v in user.items():
            embed.add_field(name=k, value=v)
        embed.add_field(name="Mention", value="<@!" + str(user.get("id")) + ">")
        # embed.add_field(name="id", value=user.get("id"))
        # embed.add_field(name="username", value=user.get("username"))
        # embed.add_field(name="stylised username", value=user.get("showUsername"))
        return embed


@cmd("userinfo", __name__, help="Get info about specified user", usage="<user>")
async def command_user_info(message: discord.Message, text: str, guild: discord.Guild, channel: discord.TextChannel,
                            **_):
    if isinstance(message.channel, discord.abc.PrivateChannel):
        user: discord.User = message.author
    else:
        if len(message.mentions) == 1:
            user: discord.Member = message.mentions[0]
        elif len(message.mentions) > 1:
            return "Please use only one mention"
        elif text.isdigit():
            try:
                user: discord.Member = guild.get_member(int(text))
            except ValueError:
                return "usage: !userinfo <mention/user id>"
            if not user:
                return "user not found"
        else:
            user: discord.Member = message.author
    embed: discord.Embed = discord.Embed(title="Info about user", color=user.color.value)
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name="User name", value=user.name, inline=True)
    embed.add_field(name="Discriminator", value=user.discriminator, inline=True)
    embed.add_field(name="Display name", value=user.display_name, inline=True)
    embed.add_field(name="ID", value=str(user.id), inline=True)
    embed.add_field(name="Joined at", value=str(user.joined_at).rsplit(".", 1)[0], inline=True)
    embed.add_field(name="Created at", value=str(user.created_at).rsplit(".", 1)[0], inline=True)
    # embed.add_field(name="Mobile status", value=user.mobile_status, inline=True)
    # embed.add_field(name="Desktop status", value=user.desktop_status, inline=True)
    # embed.add_field(name="Web status", value=user.web_status, inline=True)
    embed.add_field(name="Status", value=str(user.status), inline=True)
    embed.add_field(name="On mobile", value=user.is_on_mobile(), inline=True)
    # embed.add_field(name="", value=, inline=True)
    await channel.send(embed=embed)


@cmd("guildinfo", __name__, help="Get info about the current guild", private=False, alias=("serverinfo",))
async def command_guild_info(guild: discord.Guild, **_):
    embed = discord.Embed(title="Guild info")
    embed.add_field(name="Name", value=guild.name)
    embed.add_field(name="ID", value=str(guild.id))
    embed.add_field(name="Member count", value=str(guild.member_count))
    embed.add_field(name="Roles", value=", ".join([r.name.replace("@", "") for r in guild.roles]))
    embed.add_field(name="Voice region", value=str(guild.region))
    embed.add_field(name="Owner", value=guild.owner.display_name)
    # embed.add_field(name="", value=)
    # embed.add_field(name="", value=)

    return embed


@cmd("suggest", __name__, help="Give a suggestion about the bot or website (use in DM to use privately)",
     usage="<suggestion>", alias=("suggestion", "suggestions"))
async def command_suggest(channel: discord.TextChannel, author: discord.User, text: str, client: discord.Client,
                          config: dict, **_):
    if not text:
        return "Error: Empty suggestions aren't considered useful"
    chan: discord.TextChannel = client.get_channel(config.get("log.suggestions"))
    if chan:
        embed: discord.Embed = discord.Embed(title="Suggestion from: " + author.name + " | " + str(author.id),
                                             description=text, color=discord.Color.dark_teal())
        if isinstance(channel, discord.DMChannel):
            embed.add_field(name="Channel", value="Private from: " + author.mention)
        else:
            embed.add_field(name="Channel:", value=channel.mention)
        await chan.send(embed=embed)
        return "Suggestion listed!"
    else:
        return "Sorry there was a problem with the configuration of the bot"


@cmd("report", __name__, help="Report a problem about a user/the website/the bot/etc. to all staff (use in DM to "
                              "use privately)",
     usage="<report>", alias=("reports", "reporting"))
async def command_suggest(channel: discord.TextChannel, author: discord.User, text: str, client: discord.Client,
                          config: dict, **_):
    content = ""
    if not text:
        return "Error: Can not send empty report"
    chan: discord.TextChannel = client.get_channel(config.get("log.reports"))
    if chan:
        embed: discord.Embed = discord.Embed(title="Report from: " + author.name + " | " + str(author.id),
                                             description=text, color=discord.Color.dark_red())
        if isinstance(channel, discord.DMChannel):
            embed.add_field(name="Channel", value="Private from: " + author.mention)
        else:
            embed.add_field(name="Channel:", value=channel.mention)
        if content:
            await chan.send(content=content, embed=embed)
        else:
            await chan.send(embed=embed)
        return "Reported!"
    else:
        return "Sorry there was a problem with the configuration of the bot"
