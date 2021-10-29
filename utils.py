import datetime

import discord
import requests
import asyncio

import events
from cmds import cmd, commands
from config import config

from more_itertools import peekable

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),  # 60 * 60 * 24
    ('hours', 3600),  # 60 * 60
    ('minutes', 60),  # 60 * 1
    ('seconds', 1),
)

def display_time(seconds, granularity=3):
    result = []
    seconds = int(round(seconds))
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def display_time_minutes(seconds):
    result = []
    seconds = round(seconds)
    if seconds < 0:
        seconds = abs(seconds)
        negative = True
    else:
        negative = False
    for name, count in intervals[1:-1]:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    if negative:
        return "-" + ', '.join(result)
    else:
        return ', '.join(result)


def master(user: discord.User):
    if user.id in config.get("bot.masters", []):
        return True
    else:
        return False


def admin(user: discord.User):
    if master(user):
        return True
    if hasattr(user, 'roles'):
        if any([role.id in config.get("roles.admins", []) for role in user.roles]):
            return True
        else:
            return False
    else:
        return False


def mod(user: discord.User):
    if master(user):
        return True
    if admin(user):
        return True
    if hasattr(user, 'roles'):
        if any([role.id in config.get("roles.mods", []) for role in user.roles]):
            return True
        else:
            return False
    else:
        return False


def clean_time(time):
    return str(datetime.datetime.utcfromtimestamp(round(time)))


def build_help_dict(message: discord.Message, hidden: bool = False, mod_perms=False, admin_perms=False,
                    master_perms=False):
    modules = {}
    for k, v in commands.items():
        if v.get("forcehidden", False):
            continue
        if v["hidden"] and not hidden:
            continue
        if not isinstance(message.channel, discord.abc.PrivateChannel) and v["privateOnly"]:
            continue
        if isinstance(message.channel, discord.abc.PrivateChannel) and not v["private"]:
            continue
        if v["mod"] and not mod_perms:
            continue
        if v["admin"] and not admin_perms:
            continue
        if v["master"] and not master_perms:
            continue
        if v["module"] in modules.keys():
            modules[v["module"]][k] = v
        else:
            modules[v["module"]] = {k: v}
        modules[v["module"]][k] = v
    return modules


@events.event("on_message")
async def handle_message(message: discord.Message, stats, **_):
    stats.add_message()
    if message.content.startswith(config.get("bot.prefix")):
        stats.add_command()
    if message.mention_everyone:
        stats.add_mention_everyone()
    return


def get_word(iterator: iter, multi=False):
    word = []
    letter = next(iterator)
    if multi and letter == '"':
        for letter in iterator:
            if letter == "\\":
                next_letter = next(iterator)
                if next_letter == '"':
                    word.append(next_letter)
                else:
                    word.append(letter + next_letter)
            if letter == '"':
                return "".join(word)
            word += letter
        return "".join(word)
    word.append(letter)
    for letter in iterator:
        if letter == " " or letter == "\n":
            return "".join(word)
        word.append(letter)
    return "".join(word)


def argument_parser(text: str):
    if text == "":
        return [], {}, ""
    flags = []
    parameters = {}
    iterator = peekable(text)
    text = ""

    while iterator.peek(False) is not False:
        word = []
        next_letter = iterator.peek()
        if next_letter == "-":
            _ = next(iterator)
            next_letter = iterator.peek(None)
            if next_letter is None:
                text += "-"
                break
            if next_letter == "-":
                _ = next(iterator)  # Get rid if the character
                if iterator.peek(False) is not False:
                    parm = get_word(iterator)
                    if iterator.peek(False) is not False:
                        value = get_word(iterator, True)
                    else:
                        value = None
                    parameters[parm] = value
                else:
                    text += "--"
                    break
            else:
                flag = get_word(iterator)
                flags.append(flag)

        else:
            text += "".join([l for l in iterator])
            break

    return flags, parameters, text


def create_chunks(items, limit_items=False, limit_chars=5500):
    chunks = []
    if limit_chars:
        chars = 0
        chunk = []
        for item in items:
            if type(item) is list or type(item) is tuple:
                length = sum([len(i) for i in item])
            else:
                length = len(item)
            if chars + length > limit_chars or (limit_items and len(chunk) >= limit_items):
                chunks.append(chunk)
                chunk = [item]
                chars = len(item)
            else:
                chunk.append(item)
                chars += len(item)
        else:
            chunks.append(chunk)
        return chunks
    elif limit_items and not limit_chars:
        return [items[i * limit_items:(i + 1) * limit_items] for i in
                range((len(items) + limit_items - 1) // limit_items)]
    else:
        return items


async def paginator(client: discord.Client, chunks: (list, tuple), channel, page_maker,
                    author: discord.User = None, author_only: bool = False, start_page: int = 0,
                    delete_on_done: bool = False, max_delay: int = 300,
                    message: discord.Message = None):
    pages = len(chunks)
    page = start_page

    content, embed = page_maker(chunks[page], page, pages)
    mess = await channel.send(content=content, embed=embed)
    await mess.add_reaction("⏮")
    await mess.add_reaction("⏭")
    await mess.add_reaction("❌")

    def check(e_reaction: discord.Reaction, e_user: discord.User):
        if author_only:
            return e_reaction.message is mess and e_user is author and str(e_reaction.emoji) in ["⏭", "⏮", "❌"]
        else:
            return e_reaction.message.id == mess.id and client.user.id is not e_user.id and \
                   str(e_reaction.emoji) in ["⏭", "⏮", "❌"]

    while True:
        try:
            reaction, user = await client.wait_for('reaction_add', check=check, timeout=max_delay)
            await reaction.remove(user=user)
            if str(reaction.emoji) == "❌":
                await mess.clear_reactions()
                if delete_on_done:
                    await mess.edit(content="Done, removing message", delete_after=5, embed=None)
                    if message:
                        await message.delete()
                return
            if str(reaction.emoji) == "⏮":
                page = (page - 1) % pages
                content, embed = page_maker(chunks[page], page, pages)
                await mess.edit(content=content, embed=embed)
            if str(reaction.emoji) == "⏭":
                page = (page + 1) % len(chunks)
                content, embed = page_maker(chunks[page], page, pages)
                await mess.edit(content=content, embed=embed)
        except asyncio.TimeoutError:
            await mess.clear_reactions()
            if delete_on_done:
                await mess.edit(content="Done, removing message", delete_after=5, embed=None)
                if message:
                    await message.delete()
