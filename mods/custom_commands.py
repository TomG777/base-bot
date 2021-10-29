import asyncio
import json
import random
import re

import discord

from cmds import cmd, commands

custom_commands = json.load(open('data/commands.json'))


def save_commands(command: dict):
    json.dump(command, open('data/commands.json', 'w'), indent=2, sort_keys=True)


def sky(text: str):
    for x in range(len(text), 0, -1):
        x -= 1
        if text[x] == "{" and (text[x - 1] != "\\" if x > 0 else True):
            a = x
            for y in range(a + 1, len(text)):
                if text[y] == "}" and text[y - 1] != "\\":
                    b = y
                    if b < a:
                        return text.replace("\\{", "{").replace("\\}", "}").replace("\\|", "|")
                    text = text[:a] + random.choice(re.split(r'(?<!\\)\|', text[a + 1:b])) + text[b + 1:]
                    break
    return text.replace("\\{", "{").replace("\\}", "}").replace("\\|", "|")


async def parse_command(message: discord.Message):
    reply = custom_commands.get(message.content.split(" ", 1)[0][1:], None)
    if " " in message.content:
        text = message.content.split(" ", 1)[1]
    else:
        text = ""
    if not reply:
        return
    print(f"Called command: {message.content.split(' ', 1)[0]} | {message.author.name} {message.author.id}")
    try:
        reply = reply.replace("%user%", message.author.display_name)
        try:
            reply = reply.replace("%channel_id%", str(message.channel.id))
            reply = reply.replace("%channel%", message.channel.name)
        except AttributeError:
            pass
        try:
            reply = reply.replace("%server%_id", str(message.guild.id))
            reply = reply.replace("%guild_id%", str(message.guild.id))
            reply = reply.replace("%server%", message.guild.name)
            reply = reply.replace("%guild%", message.guild.name)
        except AttributeError:
            pass
        reply = reply.replace("%author%", message.author.mention)
        reply = reply.replace("%roles%", ", ".join([r.name.replace("@", "") for r in message.author.roles]))
        reply = reply.replace("%text%", text)
    except AttributeError:
        pass
    if "%mentions%" in reply:
        mentions = "" + " ".join([m.mention for m in message.mentions])
        reply = reply.replace("%mentions%", mentions)
    elif "%mention%" in reply:
        if len(message.mentions) == 0:
            await message.channel.send("Message requires a mention but none were found")
            return
        elif len(message.mentions) == 1:
            reply = reply.replace("%mention%", "<@!" + str(message.raw_mentions[0]) + ">")
        elif len(message.mentions) > 1:
            await message.channel.send("Message requires a mention but multiple were found")
            return
    if "{" in reply and "}" in reply and reply.count("{") == reply.count("}"):
        reply = sky(reply)
    if len(reply) != 0:
        await message.channel.send(reply)


@cmd("commands", module="custom commands", help="List all additional commands", alias=("customs",))
async def command_customs(**_):
    return "Custom commands: " + ", ".join(sorted(custom_commands.keys()))


@cmd("custominfo", module="custom commands", help="Lists options for custom commands", mod=True)
async def command_commandinfo(**_):
    embed = discord.Embed(title="Custom command options")
    embed.add_field(name="%user%", value="Mention of the user")
    embed.add_field(name="%author%", value="Name of the user")
    embed.add_field(name="%channel%", value="Channel name the command is used in")
    embed.add_field(name="%channel_id%", value="Channel id the command is used in")
    embed.add_field(name="%guild%", value="Server name the command is used in")
    embed.add_field(name="%guild_id%", value="Server id the command is used in")
    embed.add_field(name="%mention%", value="A mention of the mentioned user")
    embed.add_field(name="%mentions%", value="All mentioned users")
    embed.add_field(name="%roles%", value="Roles the user is in")
    embed.add_field(name="%text%", value="Text specified after the command")
    # embed.add_field(name="%%", value="")
    return embed


@cmd("updatecommand", module="custom commands", help="Update (or add) a command", usage="<command> <reply>", mod=True,
     alias=("updatecom", "editcommand", "editcom"), hiddenalias=("updatecom", "updcom", "upcom"))
async def command_updatecommand(text: str, **_):
    global custom_commands
    if text.count(" ") < 1:
        return "Error: invalid format, please use `.updatecommand <command> <reply>`"
    call, answer = text.strip().split(' ', 1)
    for c, co in commands.items():
        if call == c or call in co["alias"] or call in co["hiddenalias"]:
            return "Command exists in the bot as a non custom commands"
    old_command = custom_commands.get(call, None)
    custom_commands[call] = answer
    save_commands(custom_commands)
    embed = discord.Embed(title="Command updated: " + call, description=answer, color=discord.Color.green())
    if old_command is not None:
        if len(old_command) > 1020:
            embed.add_field(name="-----------------", value="Old reply:")
            embed.set_footer(text=old_command)
        else:
            embed.add_field(name="Old reply:", value=old_command)
    else:
        embed.set_footer(text="Command did not exist yet added instead")
    return embed


@cmd("addcommand", module="custom commands", help="Add a command", usage="<command> <reply>", mod=True,
     alias=("addcom",))
async def command_addcommand(text: str, **_):
    global custom_commands
    if text.count(" ") < 1:
        return "Error: invalid format, please use `.addcommand <command> <reply>`"
    call, answer = text.strip().split(' ', 1)
    for c, co in commands.items():
        if call == c or call in co["alias"] or call in co["hiddenalias"] or call in custom_commands.keys():
            return "Command already exists in the bot"
    custom_commands[call] = answer
    save_commands(custom_commands)
    embed = discord.Embed(title="Command added: " + call, description=answer, color=discord.Color.green())
    return embed


@cmd("delcommand", module="custom commands", help="Remove a command", mod=True,
     alias=("deletecommand", "removecommand"), hiddenalias=("delcom", "remcom", "deletecom", "remcommand"))
async def command_delcommand(text, author: discord.User, channel: discord.TextChannel, client: discord.Client, **_):
    global custom_commands

    def check(mess):
        if not mess.channel == channel or not mess.author == author:
            return False
        return True

    if text in custom_commands.keys():
        await channel.send("Are you sure you want to remove " + text + "? type `.confirm` to confirm")
        try:
            msg = await client.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return "Removal cancelled"
        else:
            if msg.content == ".confirm":
                deleted = custom_commands.pop(text, None)
                save_commands(custom_commands)
                embed = discord.Embed(title="Command deleted: " + text, description=deleted, color=discord.Color.red())
                return embed
            else:
                return "Removal cancelled"
    else:
        return "Error: command not found"


@cmd("botsay", module="custom commands", help="Let the bot say something in a pretty embed", usage="<message>",
     mod=True)
async def command_botsay(message: discord.Message, text: str, channel: discord.TextChannel,
                         client: discord.Client, **_):
    await message.delete()
    if text.startswith("<#"):
        try:
            reply_channel = client.get_channel(int(text.split(" ", 1)[0][2:-1]))
            reply_text = text.split(" ", 1)[1]
        except ValueError:
            reply_channel = channel
            reply_text = text
        if not reply_channel:
            reply_channel = channel
            reply_text = text.split(" ", 1)[1]
    else:
        reply_channel = channel
        reply_text = text
    embed: discord.Embed = discord.Embed(title="Bot announcement:", description=reply_text, color=0x000080)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/451475652823220228/553944349231153173/botty.png")
    await reply_channel.send(embed=embed)
