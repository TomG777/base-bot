import asyncio
import json
import re
import time
from collections import defaultdict

import discord
import pytimeparse

import utils
from cmds import cmd
from events import event


def defaultdict_from_dict(d):
    nd = lambda: defaultdict(nd)
    ni = nd()
    ni.update(d)
    return ni


temp_things = json.load(open('data/temp_things.json'), object_hook=defaultdict_from_dict)


def save_temps():
    json.dump(temp_things, open('data/temp_things.json', 'w'), sort_keys=True, indent=2)


# noinspection PyDefaultArgument
async def unban(guild: discord.Guild, user: discord.User, client: discord.Client, time_stamp: int = 0,
                config: dict = {}):
    if not user:
        return False
    if not guild:
        return False
    channel = client.get_channel(config.get("log.moderation"))
    if time_stamp < time.time():
        temp_things.get("ban", {}).get(str(guild.id), {}).pop(str(user.id))
        save_temps()
        try:
            await guild.unban(user, reason="Temp ban period is over")
        except discord.Forbidden:
            if channel:
                await channel.send("attempted to unban a user but no permissions")
        except discord.HTTPException:
            pass
        else:
            if channel:
                await channel.send("Unbanned " + user.display_name)
    else:
        delay = time_stamp - time.time()
        await asyncio.sleep(delay)
        if temp_things["ban"][str(guild.id)][str(user.id)] == time_stamp:
            temp_things.get("ban", {}).get(str(guild.id), {}).pop(str(user.id), 0)
            save_temps()
            try:
                await guild.unban(user, reason="Temp ban period is over")
            except discord.Forbidden:
                if channel:
                    await channel.send("attempted to unban a user but no permissions")
            except discord.HTTPException:
                pass
            else:
                if channel:
                    await channel.send("Unbanned " + user.display_name)
                else:
                    print("missing channel for unban")


# noinspection PyDefaultArgument
async def unmute(member: discord.Member, client: discord.Client, time_stamp: int = 0, config: dict = {}):
    print("unmute")
    if not member:
        return False
    channel = client.get_channel(config.get("log.moderation"))
    guild: discord.Guild = member.guild
    muterole = guild.get_role(config.get("moderation.mute_role"))
    if isinstance(time_stamp, defaultdict):
        return
    elif time_stamp < time.time():
        temp_things.get("mute", {}).get(str(guild.id), {}).pop(str(member.id))
        save_temps()
        try:
            await member.remove_roles(muterole, reason="Mute period is over")
        except discord.Forbidden:
            if channel:
                await channel.send("attempted to unmute a user but no permissions")
        except discord.HTTPException:
            pass
        else:
            if channel:
                await channel.send("Unmuted " + member.display_name + " " + member.mention)
            else:
                print("missing channel for unmute")
    else:
        delay = time_stamp - time.time()
        await asyncio.sleep(delay)
        if temp_things["mute"][str(guild.id)][str(member.id)] == time_stamp:
            temp_things.get("mute", {}).get(str(guild.id), {}).pop(str(member.id), 0)
            save_temps()
            try:
                await member.remove_roles(muterole, reason="Mute period is over")
            except discord.Forbidden:
                if channel:
                    await channel.send("attempted to unmute a user but no permissions")
            except discord.HTTPException:
                pass
            else:
                if channel:
                    await channel.send("Unmuted " + member.display_name + " " + member.mention)


@event("on_first_ready")
async def setup_unthing_loop(loop: asyncio.AbstractEventLoop, client: discord.Client, config: dict, **_):
    print("Unthing loop started")
    for guildid, items in temp_things["ban"].items():
        guild: discord.Guild = client.get_guild(int(guildid))
        for userid, timestamp in items.items():
            if not (isinstance(timestamp, int) or isinstance(timestamp, float)):
                temp_things["ban"][guildid].pop()
            user: discord.User = client.get_user(int(userid))
            if user:
                asyncio.ensure_future(unban(guild, user, client, timestamp), loop=loop)

    for guildid, items in temp_things["mute"].items():
        guild: discord.Guild = client.get_guild(int(guildid))
        for userid, timestamp in items.items():
            user: discord.User = guild.get_member(int(userid))
            asyncio.ensure_future(unmute(user, client, timestamp, config), loop=loop)
    print("unthing loop done")


def get_member(search: str, message: discord.Message = None):
    if len(message.mentions) > 0 and search.startswith("<@") and search.endswith(">"):
        return message.mentions[0]
    else:
        user = None
        try:
            user_id = abs(int(search))
            user = message.guild.get_member(user_id)
            if not user:
                user = message.guild.get_member_named(search)
        except ValueError:
            user = message.guild.get_member_named(search)
        finally:
            if not user:
                return None
    return user


def get_user(search: str, client: discord.Client, message: discord.Message = None):
    if len(message.mentions) > 0 and search.startswith("<@") and search.endswith(">"):
        user = message.mentions[0]
    else:
        user = None
        try:
            user_id = abs(int(search))
            user = client.get_user(user_id)
            if not user:
                user = message.guild.get_member_named(search)
        except ValueError:
            user = message.guild.get_member_named(search)
        finally:
            if not user:
                return None
    return user


@cmd("kick", "moderation", mod=True, help="Kick somebody in the bum", usage="<user> [reason]", private=False)
async def command_kick(message: discord.Message, author: discord.Member, channel: discord.TextChannel, text: str, **_):
    user: discord.Member = None
    if not text:
        return "Please enter a user to kick (and optionally a reason)"
    else:
        splits = text.split(" ", 1)
        if len(splits) == 1:
            search = splits[0]
            reason = None
        else:
            search = splits[0]
            reason = splits[1]
    if search:
        user: discord.User = get_member(search, message)
    if not user:
        return "Error: No user found for text: `" + search + "`"
    try:
        await user.kick(reason="Kick command triggered by: " + author.display_name + " reason: " + str(reason))
    except discord.Forbidden:
        await channel.send("Attempted kick ban a user but no permissions")
    except discord.HTTPException:
        await channel.send("Unable to kick user, something went odd")
    else:
        if reason:
            await user.send(
                "You have been kicked from the morningstreams discord server by: " + author.mention +
                "\nFor the following reason: " + reason)
        else:
            await user.send(
                "You have been kicked from the morningstreams discord server by: " + author.mention +
                "\nNo reason was specified")
        embed = discord.Embed(color=discord.Colour.red())
        embed = embed.set_author(name="Member kicked", icon_url=user.avatar_url)
        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Moderator", value=author.mention)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        await channel.send(embed=embed)


async def cancel(message: discord.Message):
    await message.edit(content="Cancelled", embed=None)
    await message.clear_reactions()
    await asyncio.sleep(15)
    await message.delete()


def decode_com(text: str):
    if not text:
        return "Please gib any input"
    if text.count(" ") == 0:
        return "Please give enough inputs"
    if text.startswith("\""):
        if text[1:].count("\"") <= text.count("\\\""):
            return "Error: Found opening `\"` without a closing one"
        search, duration = re.split(r'(?<!\\)\"', text[1:], 1)
    else:
        search, duration = text.split(" ", 1)
    duration = duration.strip()
    if duration.startswith("\""):
        if duration[1:].count("\"") <= duration.count("\\\""):
            return "Error: Found opening `\"` without a closing one"
        else:
            duration, reason = re.split(r'(?<!\\)\"', duration[1:], 1)
    elif duration.count(" "):
        duration, reason = duration.split(" ", 1)
    else:
        reason = None

    search = search.replace("\\\"", "\"")
    return search, duration, reason


@cmd("tempban", "moderation", mod=True, help="Temp ban somebody", usage="<user> <duration> [reason]", private=False)
async def command_temp_ban(message: discord.Message, guild: discord.Guild, channel: discord.TextChannel,
                           author: discord.Member, client: discord.Client, text: str, config: dict, **_):
    def check_confirm(check_reaction, check_user):
        if check_reaction.message.id != mess.id:
            return False
        if not utils.mod(check_user):
            return False
        if not (str(check_reaction.emoji) == "✅" or check_reaction.emoji.id == 598078090349903872):
            return False
        return True

    user: discord.Member = None
    decoded = decode_com(text)
    if isinstance(decoded, str):
        return decoded
    else:
        search, duration, reason = decoded
    # Find the correct user
    if search:
        user = get_member(search, message)
    if not user:
        return "Error: No user found for text: `" + search + "`"

    # Find the correct duration
    duration = duration.replace("\\\"", "\"")
    if duration:
        seconds = pytimeparse.parse(duration)
        if not seconds:
            return "Error: Can not parse duration correctly: " + duration
        formatted = utils.display_time(seconds)
    else:
        return "Error: Something went wrong with parsing the duration"

    # Send confirmation message
    embed = discord.Embed(color=discord.Colour.red())
    embed = embed.set_author(name="Temp ban member?", icon_url=user.avatar_url)
    embed.add_field(name="User", value=user.mention)
    embed.add_field(name="Moderator", value=author.mention)
    embed.add_field(name="Duration", value=formatted)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    mess: discord.Message = await channel.send(embed=embed)
    await mess.add_reaction("✅")
    await mess.add_reaction("❌")

    # check confirmation
    try:
        reaction, _ = await client.wait_for('reaction_add', timeout=60.0, check=check_confirm)
    except asyncio.TimeoutError:
        return await cancel(mess)
    else:
        if reaction.emoji == "❌":
            return await cancel(mess)
    # send confirmations and perform action
    chan: discord.TextChannel = client.get_channel(config.get("log.mainChannel"))
    await mess.delete()
    embed = embed.set_author(name="Temp banning member", icon_url=user.avatar_url)
    await channel.send(embed=embed)
    await chan.send(embed=embed)
    # perform action
    unban_time = int(time.time()) + seconds
    temp_things["ban"][str(guild.id)][str(user.id)] = unban_time
    save_temps()
    try:
        await user.ban(reason="Temp ban command triggered for: " + duration)
    except discord.Forbidden:
        await channel.send("Attempted to temp ban a user but no permissions")
    except discord.HTTPException:
        await channel.send("Unable to ban user, already banned, new time is noted")
    else:
        if reason:
            await user.send(
                "You have been temporarily banned from the morningstreams discord server for: `" + duration + " `by: " +
                author.mention + "\nFor the following reason: " + reason)
        else:
            await user.send(
                "You have been temporarily banned from the morningstreams discord server for: `" + duration + " `by: " +
                author.mention + "\nNo reason was specified")
        await channel.send("temp banned: " + user.display_name)
    await unban(guild, user, client, unban_time, config)


@cmd("tempmute", "moderation", mod=True, help="Temp mute somebody", usage="<user> <duration> [reason]", private=False)
async def command_temp_mute(message: discord.Message, guild: discord.Guild, channel: discord.TextChannel,
                            author: discord.Member, client: discord.Client, text: str, config: dict, **_):
    def check_confirm(check_reaction, check_user):
        if check_reaction.message.id != mess.id:
            print(message.id, check_reaction.message.id)
            return False
        if not utils.mod(check_user):
            return False
        if not (str(check_reaction.emoji) == "✅" or str(check_reaction.emoji) == "❌"):
            return False
        return True

    user: discord.Member = None
    decoded = decode_com(text)
    if isinstance(decoded, str):
        return decoded
    else:
        search, duration, reason = decoded
    # Find the correct user
    if search:
        user = get_member(search, message)
    if not user:
        return "Error: No user found for text: `" + search + "`"

    # Find the correct duration
    duration = duration.replace("\\\"", "\"")
    if duration:
        seconds = pytimeparse.parse(duration)
        if not seconds:
            return "Error: Can not parse duration correctly: " + duration
        formatted = utils.display_time(seconds)
    else:
        return "Error: Something went wrong with parsing the duration"

    # Send confirmation message
    embed = discord.Embed(color=discord.Colour.red())
    embed = embed.set_author(name="Temp mute member?", icon_url=user.avatar_url)
    embed.add_field(name="User", value=user.mention)
    embed.add_field(name="Moderator", value=author.mention)
    embed.add_field(name="Duration", value=formatted)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    if seconds >= 600:
        mess: discord.Message = await channel.send(embed=embed)
        await mess.add_reaction("✅")
        await mess.add_reaction("❌")

        # check confirmation
        try:
            reaction, _ = await client.wait_for('reaction_add', timeout=60.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await cancel(mess)
        else:
            if str(reaction.emoji) == "❌":
                return await cancel(mess)
            else:
                await mess.delete()
    # send confirmations and perform action
    chan: discord.TextChannel = client.get_channel(config.get("log.mainChannel"))
    embed = embed.set_author(name="Temp muting member", icon_url=user.avatar_url)
    # await channel.send(embed=embed)
    await chan.send(embed=embed)
    # perform action
    unmute_time = int(time.time()) + seconds
    temp_things["mute"][str(guild.id)][str(user.id)] = unmute_time
    save_temps()
    muterole = guild.get_role(config.get("moderation.mute_role"))
    try:
        await user.add_roles(muterole, reason="Temp mute command triggered for: " + duration)
    except discord.Forbidden:
        await channel.send("Attempted to temp mute a user but no permissions")
    except discord.HTTPException:
        await channel.send("Unable to mute user, already muted, new time is noted")
    else:
        if reason:
            await user.send(
                "You have been temporarily muted from the morningstreams discord server for: `" + duration + " `by: " +
                author.mention + "\nFor the following reason: " + reason)
        else:
            await user.send(
                "You have been temporarily muted from the morningstreams discord server for: `" + duration + " `by: " +
                author.mention + "\nNo reason was specified")
        await channel.send("Muted: " + user.display_name)
    await unmute(user, client, unmute_time, config)


@cmd("unban", "moderation", help="Unban a user", usage="<user>", mod=True)
async def command_unban(message: discord.Message, channel: discord.TextChannel, guild: discord.Guild, text: str,
                        client: discord.Client, **_):
    if not text:
        return "Missing input"
    user = get_user(text, client=client, message=message)
    if not user:
        return "Error: No user found for text: `" + text + "`"
    try:
        await guild.unban(user, reason="Unban command triggered")
    except discord.Forbidden:
        await channel.send("Attempted to unban a user but no permissions")
    except discord.HTTPException:
        await channel.send("Unable to unban user, not banned")
    else:
        await channel.send("Unbanned: " + user.display_name)
    temp_things["ban"][str(guild.id)].pop(str(user.id), 0)
    save_temps()


@cmd("unmute", "moderation", help="Unmute a user", usage="<user>", mod=True, private=False)
async def command_unban(message: discord.Message, channel: discord.TextChannel, guild: discord.Guild, text: str,
                        config: dict, **_):
    if not text:
        return "Missing input"
    user: discord.Member = get_member(text, message)
    if not user:
        return "Error: No user found for text: `" + text + "`"
    muterole = guild.get_role(config.get("moderation.mute_role"))
    try:
        await user.remove_roles(muterole, reason="Unmute command triggered")
    except discord.Forbidden:
        await channel.send("Attempted to unmute a user but no permissions")
    except discord.HTTPException:
        await channel.send("Unable to unmute user, not muted")
    else:
        await channel.send("Unmuted: " + user.display_name)
    temp_things["mute"][str(guild.id)].pop(str(user.id), 0)
    save_temps()


@cmd("ban", "moderation", help="Ban a user", usage="<user> [reason]", mod=True, private=False)
async def command_ban(message, text, guild, author: discord.Member, channel, client, config, **_):
    user: discord.Member = None
    if not text:
        return "Please enter a user to ban (and optionally a reason)"
    else:
        splits = text.split(" ", 1)
        if len(splits) == 1:
            search = splits[0]
            reason = None
        else:
            search = splits[0]
            reason = splits[1]
    if search:
        user = get_user(search, client, message)
    if not user:
        return "Error: No user found for text: `" + search + "`"
    try:
        await user.ban(reason="Ban command triggered by: " + author.display_name + " reason: " + str(reason))
    except discord.Forbidden:
        await channel.send("Attempted to ban a user but no permissions")
    except discord.HTTPException:
        await channel.send("Unable to ban user, already banned, (unban time removed)")
        temp_things.get("ban", {}).get(str(guild.id), {}).pop(str(user.id), 0)
        save_temps()
    else:
        if reason:
            await user.send(
                "You have been banned from the morningstreams discord server by: " + author.mention +
                "\nFor the following reason: " + reason)
        else:
            await user.send(
                "You have been banned from the morningstreams discord server by: " + author.mention +
                "\nNo reason was specified")
        embed = discord.Embed(color=discord.Colour.red())
        embed = embed.set_author(name="Member banned", icon_url=user.avatar_url)
        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Moderator", value=author.mention)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        await channel.send(embed=embed)
        chann = client.get_channel(config.get("log.moderation"))
        await chann.send(embed=embed)
        temp_things.get("ban", {}).get(str(guild.id), {}).pop(str(user.id), 0)
        save_temps()


@cmd("mute", "moderation", help="Mute a user", usage="<user> [reason]", mod=True, private=False)
async def command_mute(message, text, guild, author: discord.Member, channel, client, config, **_):
    user: discord.Member = None
    if not text:
        return "Please enter a user to mute (and optionally a reason)"
    else:
        splits = text.split(" ", 1)
        if len(splits) == 1:
            search = splits[0]
            reason = None
        else:
            search = splits[0]
            reason = splits[1]
    if search:
        user = get_member(search, message)
    if not user:
        return "Error: No user found for text: `" + search + "`"
    try:
        muterole = guild.get_role(config.get("moderation.mute_role"))
        await user.add_roles(muterole, reason="Mute command triggered by: " + author.display_name + " reason: " +
                                              str(reason))
    except discord.Forbidden:
        await channel.send("Attempted to mute a user but no permissions")
    except discord.HTTPException:
        await channel.send("Unable to mute user, already muted, (unmute time removed)")
        temp_things.get("mute", {}).get(str(guild.id), {}).pop(str(user.id), 0)
        save_temps()
    else:
        if reason:
            await user.send(
                "You have been muted in the morningstreams discord server by: " + author.mention +
                "\nFor the following reason: " + reason)
        else:
            await user.send(
                "You have been muted in the morningstreams discord server by: " + author.mention +
                "\nNo reason was specified")
        embed = discord.Embed(color=discord.Colour.red())
        embed = embed.set_author(name="Member muted", icon_url=user.avatar_url)
        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Moderator", value=author.mention)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        await channel.send(embed=embed)
        chann = client.get_channel(config.get("log.moderation"))
        await chann.send(embed=embed)
        temp_things.get("mute", {}).get(str(guild.id), {}).pop(str(user.id), 0)
        save_temps()


@cmd("clear", "moderation", mod=True, help="Clear unwanted messages from a channel")
async def command_clear(message: discord.Message, channel: discord.TextChannel, **_):
    await message.delete()
    data = {"655139420810379284": [655139776441352204]}
    channel_data = data.get(str(channel.id), [])

    def check(m):
        return m.id not in channel_data

    if not channel_data:
        return "Error: this channel is not set up for automatic clearing"
    deleted = await channel.purge(limit=100, check=check)
    mess = await channel.send('Cleared {} message(s)'.format(len(deleted)), delete_after=10)
