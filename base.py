import asyncio
import importlib
import logging
import random
import socket
import sys
import time
import urllib

from mods import custom_commands
from mods import *
from static_mods import *

import discord
from discord.ext import tasks
import requests
import urllib3

import config
import events
import statistics
import utils
from cmds import commands, cmd

logLevel = config.config.get("bot.logLevel", "info").lower()
if logLevel == "critical":
    logging.basicConfig(level=logging.CRITICAL)
elif logLevel == "error":
    logging.basicConfig(level=logging.ERROR)
elif logLevel == "warning":
    logging.basicConfig(level=logging.WARNING)
elif logLevel == "info":
    logging.basicConfig(level=logging.INFO)
elif logLevel == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)

# intents
intents = discord.Intents.all()

# client that discord uses
client: discord.Client = discord.Client(intents=intents)
stats = statistics.Stats(client)
prefix: str = config.config.get("bot.prefix", "!")
prefix_length: int = len(prefix)
restart_file: str = config.config.get("bot.restartFile", "data/restart.txt")
selfbot: bool = config.config.get("bot.selfbot", False)
masters = config.config.get("bot.masters", [])
print(masters)

# assign the channel IDs for the used channels, and also check that they are ints
fallback_channel: int = config.config.get("bot.errorFallbackChannel", None)
if not isinstance(fallback_channel, int):
    fallback_channel = None
invites_channel: int = config.config.get("invites.channel", None)
if not isinstance(invites_channel, int):
    invites_channel = None
invites_talk_channel: int = config.config.get("channels.invitestalk", None)
if not isinstance(invites_talk_channel, int):
    invites_talk_channel = None
log_channel: int = config.config.get("log.mainChannel", None)
if not isinstance(log_channel, int):
    log_channel = None
private_channel = config.config.get("log.private", None)
if not isinstance(private_channel, int):
    private_channel = None

first_ready = True


@client.event
async def on_ready():
    """
    discord.py event to process the connection being ready,
    this usually happens when the bot starts or a connection error occurred while running.
    This will display information to console, if set handle the presence and log things to a channel.
    """
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    stats.set_started_time()
    channel = config.config.get("log.startedReportChannel", None)
    if channel:
        channel = client.get_channel(channel)
        print(channel)
        await channel.send("Restarted at: " + utils.clean_time(stats.get_started_time()))
    # client.invite_loop = invite_loop.Loop(client, config)
    loop = asyncio.get_event_loop()
    global first_ready
    if first_ready:
        first_ready = False
        for event in events.events.get("on_first_ready", {}).values():
            try:
                asyncio.ensure_future(event(client=client, stats=stats, config=config.config, loop=loop), loop=loop)
            except Exception as e:
                print(e)
    for event in events.events.get("on_ready", {}).values():
        try:
            asyncio.ensure_future(event(client=client, stats=stats, config=config.config, loop=loop), loop=loop)
        except Exception as e:
            print(e)


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """
    discord.py event to process reaction additions

    :param user: The user posting the reaction
    :type user: discord.User
    :param reaction: The reaction being added
    :type reaction: discord.Reaction
    """
    # Let utils.handle_reaction_add process the addition of the reaction
    # await utils.handle_reaction_add(reaction, user, client)
    for event in events.events.get("on_reaction_add", {}).values():
        try:
            await event(reaction=reaction, user=user, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_guild_join(guild):
    for event in events.events.get("on_guild_join", {}).values():
        try:
            await event(guild=guild, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_member_remove(member: discord.Member, **_):
    for event in events.events.get("on_member_remove", {}).values():
        try:
            await event(member=member, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_member_join(member: discord.Member):
    for event in events.events.get("on_member_join", {}).values():
        try:
            await event(member=member, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_raw_reaction_add(payload):
    for event in events.events.get("on_raw_reaction_add", {}).values():
        try:
            await event(payload=payload, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_raw_reaction_remove(payload):
    for event in events.events.get("on_raw_reaction_remove", {}).values():
        try:
            await event(payload=payload, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_raw_message_edit(payload):
    for event in events.events.get("on_raw_message_edit", {}).values():
        try:
            await event(payload=payload, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_raw_message_delete(payload):
    for event in events.events.get("on_raw_message_delete", {}).values():
        try:
            await event(payload=payload, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_message_delete(message: discord.Message):
    for event in events.events.get("on_raw_message_edit", {}).values():
        try:
            await event(message=message, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_voice_state_update(member, before, after):
    for event in events.events.get("on_voice_state_update", {}).values():
        try:
            await event(member=member, before=before, after=after, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)


@client.event
async def on_message(message: discord.Message):
    """
    discord.py event to process a new message.

    This is the main thing inside the bot. This is where commands get processed and other magic happens.

    :param message: The message that the bot will be processing
    :type message: discord.Message
    """
    # Let utils.handle_message process some stats and other constants for the message
    # await utils.handle_message(message, client, stats)

    for event in events.events.get("on_message", {}).values():
        try:
            await event(message=message, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)

    for channel in events.channel_events.get(message.channel.id, {}).values():
        try:
            await channel(message=message, client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)

    # If the bot is a self bot only care about your own messages (less useful in morningbot)
    if selfbot:
        if message.author.id not in masters:
            return
    else:
        # If not a self bot log private messages to a channel so people trolling/abusing/needing help can be handled
        if isinstance(message.channel, discord.abc.PrivateChannel) and message.author.id != client.user.id:
            # check if a private_channel (destination) is set and send info about the message there
            if private_channel:
                chan: discord.TextChannel = client.get_channel(private_channel)
                embed: discord.Embed = discord.Embed(title="Private message from: " + message.author.name + " | " +
                                                           str(message.author.id), description=message.content)
                await chan.send(embed=embed)
    # Ignore messages in invites_channel (No command allowed to avoid abuse)
    if message.channel.id == invites_channel:
        return
    # If the command start with the bot prefix handle commands and stuff
    elif message.content.startswith(prefix):
        # Filter out the prefix
        stripped = message.content[prefix_length:].strip()
        # Try to split the command in the command call, and the following text/arguments
        try:
            call, text = stripped.split(' ', 1)
            args = text.split(' ')
        except ValueError:
            call = stripped
            args = []
            text = ''
        # If a selfbot don't care about permissions since allowed users (master) is already checked
        if selfbot:
            admin: bool = True
            master: bool = True
            mod: bool = True
        else:
            admin: bool = utils.admin(message.author)
            mod: bool = utils.mod(message.author)
            master: bool = utils.master(message.author)
        found: bool = False
        for argument, command in commands.items():
            # If this call does not correspond to any of the commands/aliases skip to the next
            l_call = call.lower()
            if l_call != argument.lower() and l_call not in command.get("alias", []) and \
                    l_call not in command.get("hiddenalias", []):
                continue
            if command.get("guild"):
                if message.guild.id not in command.get("guild", []):
                    return
            if command.get("guilds_blacklist"):
                if message.guild.id in command.get("guilds_blacklist", []):
                    return
            alt_roles = command.get("alt_roles", [])
            alt_users = command.get("alt_users", [])
            if alt_roles or alt_users:
                if any([role in alt_roles for role in message.author.roles]) or message.author.id in alt_users:
                    pass
                else:
                    if command.get("mod_overwrite", False):
                        await message.channel.send(
                            "Warning: You do not have the proper permissions to use this command")
                        return
                    else:
                        # Check if author has the correct rank otherwise reply a warning
                        if (not mod and command["mod"]) or (not admin and command["admin"]) or (
                                not master and command["master"]):
                            await message.channel.send(
                                "Warning: You do not have the proper permissions to use this command")
                            return
            else:
                # Check if author has the correct rank otherwise reply a warning
                if (not mod and command["mod"]) or (not admin and command["admin"]) or (
                        not master and command["master"]):
                    await message.channel.send("Warning: You do not have the proper permissions to use this command")
                    return
            # If this command is not allowed in private while the channel is private skip
            if command["private"] is False and isinstance(message.channel, discord.abc.PrivateChannel):
                await message.author.send("Warning: This command is command can not be used in private messages")
                return
            # If the command is only allowed in private but the channel is not skip
            if command["privateOnly"] and not isinstance(message.channel, discord.abc.PrivateChannel):
                await message.channel.send("Warning: This command can only be used in private messages to the bot")
                return
            # If the command it triggered by a bot but a bot is not allowed skip
            if message.author.bot and not command["bots"]:
                continue
            found = True
            # If the command should be logged to console do this
            if config.config.get("bot.printCommands", False):
                try:
                    print_message = f"Called command: {argument} | {message.author.name} {message.author.id}"
                    append = ""
                    if message.guild:
                        print_message += f" | {message.guild.name} {message.guild.id}"
                    else:
                        append += " no guild"
                    if isinstance(message.channel, discord.TextChannel):
                        print_message += f" | {message.channel.name} {message.channel.id}"
                    elif isinstance(message.channel, discord.DMChannel):
                        print_message += f" | Private channel {message.channel.id} with " \
                                         f"{str(message.channel.recipient)}"
                    elif isinstance(message.channel, discord.GroupChannel):
                        print_message += f" | Group channel {message.channel.id} Owner by: " \
                                         f"{str(message.channel.owner)} with: " \
                                         f"{[str(u) for u in message.channel.recipients]}"
                    else:
                        append += " no channel"

                    print(print_message + append)
                except Exception as e:
                    print(e)
            # Try to run the command and get the response
            try:
                response = await command.get("f")(message=message, author=message.author, channel=message.channel,
                                                  guild=message.guild, text=text, args=args, config=config.config,
                                                  stats=stats, client=client)
            # If something goes wrong log to console
            except Exception as e:
                print(e)
            # If nothing went wrong do the following
            else:
                # If we got a response (some commands don't return anything and handle all messaging internally
                if response is not None and response != "":
                    # Send the response checking whether it is an embed or not
                    try:
                        if isinstance(response, tuple):
                            if isinstance(response[0], discord.Embed):
                                await message.channel.send(response[1], embed=response[0])
                            elif isinstance(response[1], discord.Embed):
                                await message.channel.send(response[0], embed=response[1])
                            else:
                                for r in response:
                                    await message.channel.send(r)
                        elif isinstance(response, discord.Embed):
                            await message.channel.send(embed=response)
                        else:
                            await message.channel.send(response)
                    # discord.Forbidden no write access in channel
                    except discord.Forbidden:
                        if fallback_channel:
                            fallback = "No permission for command printing output here\n"
                            try:
                                fallback += (f"Called command: {argument} | {message.author.name} " +
                                             f"{message.author.id} | {message.guild.name} {message.guild.id}:" +
                                             f"{message.channel.name} {message.channel.id}")
                            except ValueError:
                                try:
                                    fallback += (
                                            f"Called command: {argument} | {message.author.name} {message.author.id} " +
                                            f"| {message.channel.name} {message.channel.id}")
                                except ValueError:
                                    fallback += (
                                            f"Called command: {argument} | {message.author.name} {message.author.id} " +
                                            f"| no guild or channel")
                            await client.get_channel(fallback_channel).send(fallback)
                            await client.get_channel(fallback_channel).send(response)
                    # Usually the response is too long (over 2k chars
                    except discord.HTTPException as e:
                        await message.channel.send("HTTPException (message length: " + str(len(response)) + ")")
                        print(e)
                    # embed or string was not given, usually something went really wrong, should not happen at al
                    except discord.InvalidArgument:
                        if fallback_channel:
                            await client.get_channel(fallback_channel).send("Invalid argument on command:")
                            await client.get_channel(fallback_channel).send(message.content)
        # If no command matched the given one check the custom commands
        if not found:
            await custom_commands.parse_command(message)


@cmd("updateglobals", "core", help="Update some internal bot values", master=True, hidden=True)
async def command_updateglobals(**_):
    # Refresh the internal values from the config
    global prefix, prefix_length, selfbot, masters, fallback_channel, invites_channel, log_channel, \
        private_channel, restart_file
    importlib.reload(config)
    prefix = config.config.get("bot.prefix", "!")
    prefix_length = len(prefix)
    masters = config.config.get("bot.masters", [])
    fallback_channel = config.config.get("bot.errorFallbackChannel", None)
    log_channel = config.config.get("log.logChannel", None)
    private_channel = config.config.get("log.privateChannel", None)
    selfbot = config.config.get("bot.selfbot", False)
    restart_file = config.config.get("bot.restartFile", "data/restart.txt")


@cmd("eval", "core", help="Use python str(eval()) to evaluate something", usage="<arguments>", master=True, hidden=True)
async def command_eval(message: discord.Message, text: str, channel: discord.TextChannel, guild: discord.Guild, **_):
    if config.config.get("bot.eval", False):
        # Little hack to stop pycharm from nagging about unused parameter
        _, _, _ = message, channel, guild
        if text == '':
            return "Error: No arguments"
        else:
            python = "```py\n{}\n```"
            try:
                result = eval(text.strip('`'))
            except Exception as e:
                return python.format(type(e).__name__ + ": " + str(e))
            else:
                return str(result)
    else:
        return "Error: command disabled"


@cmd("execeval", "core", help="Use python exec and  str(eval()) to evaluate something", usage="<exec>+\\n<eval>",
     master=True, hidden=True)
async def command_execeval(message: discord.Message, text: str, channel: discord.TextChannel, guild: discord.Guild,
                           **_):
    if config.config.get("bot.eval", False):

        exe, eva = text.rsplit("\n", 1)
        if text == '':
            return "Error: No arguments"
        else:
            python = "```py\n{}\n```"
            try:
                for ex in exe.split("\n"):
                    exec(ex)
                result = eval(eva.strip('`'))
            except Exception as e:
                return python.format(type(e).__name__ + ": " + str(e))
            else:
                return str(result)
    else:
        return "Error: command disabled"


@cmd("evall", "core", help="Use python repr(eval()) to evaluate expression", usage="<expression>", master=True,
     hidden=True)
async def bot_evall(message: discord.Message, text, **_):
    if config.config.get("bot.eval", False):
        # Little hack to stop pycharm from nagging about unused parameter
        _ = message
        if text == '':
            return "Error: No arguments"
        else:
            python = "```py\n{}\n```"
            try:
                result = eval(text.strip('`'))
            except Exception as e:
                return python.format(type(e).__name__ + ": " + str(e))
            else:
                return repr(result)
    else:
        return "Error: command disabled"


@cmd("reload", "core", help="Reload modules", admin=True)
async def command_reload(channel, **_):
    # Loop through the imports and reload all things in the mods file (basically all commands)
    for module in sys.modules.values():
        try:
            if hasattr(module, "__file__") and module.__file__ is not None and ("mods" in module.__file__ and not "static_mods" in module.__file__):
                try:
                    importlib.reload(module)
                except TypeError:
                    pass
                except Exception as e:
                    await channel.send(str(e))
                    print(e)
        except AttributeError as e:
            print("Attribute error:")
            print(e)
            pass
    # And also reload utils and update the config
    importlib.reload(utils)
    importlib.reload(config)
    for event in events.events.get("reload", {}).values():
        try:
            await event(client=client, stats=stats, config=config.config)
        except Exception as e:
            print(e)
    return "Reloaded"


@cmd("reload-test", "core", help="Reload test module", master=True, forcehidden=True, hiddenalias=("rtest",))
async def command_reload(**_):
    # Reload the testing module, not often used
    importlib.reload(testing)
    return "Reloaded"


@cmd("reloadmodule", "core", help="Reload <module>", usage="<module>", master=True, hidden=True)
async def command_reload_modules(text, **_):
    # Reload a specific module/import
    try:
        mod = sys.modules[text]
    except KeyError:
        try:
            text = "mods." + text
            mod = sys.modules[text]
        except KeyError:
            return "Error: Module not found"
    importlib.reload(mod)
    return "Reloaded: " + str(mod.__name__)


@cmd("import", "core", help="import <module>", usage="<module>", master=True, hidden=True)
async def command_import(text, **_):
    try:
        # Import a specific module
        mod = importlib.import_module(text)
        globals()[text] = mod
        return "Imported: " + str(mod)
    except ImportError as e:
        return str(e)


@cmd("stop", "core", help="Stop the bot", admin=True)
async def command_stop(channel, **_):
    # Stop the bot and write to a file that the restart script reads that the bot should not be started again
    game = discord.Game(name="Stopping")
    status = discord.Status('dnd')
    with open(restart_file, 'w') as rsfile:
        rsfile.write("stop")
    try:
        await client.change_presence(activity=game, status=status)
    except Exception as e:
        await channel.send(str(e))
        print(e)
    await client.logout()
    await client.close()
    sys.exit(1)


@cmd("restart", "core", help="Restart the bot", admin=True)
async def command_restart(channel: discord.TextChannel, **_):
    # Just exit the process so the restart script will bring the bot up on a completely new instance
    await channel.send("I'll be back (hopefully)")
    try:
        await client.change_presence(status=discord.Status.idle)
    except Exception:
        raise
    await client.close()
    sys.exit(1)


@cmd("help", "core", help="Get this help, use filter to limit to specific commands/mods", usage="[filter]", bots=True)
async def command_help(message: discord.Message, text: str, **_):
    # If -h is given also display hidden commands
    if text.startswith("-h"):
        hidden = True
        text = text.lstrip("-h").strip()
    else:
        hidden = False
    # Check some filters to be able to show lower tier help response for higher tier
    if text.startswith("-n"):
        text = text.lstrip("-n").strip()
        mod = False
        admin = False
        master = False
    elif text.startswith("-m"):
        text = text.lstrip("-m").strip()
        mod = utils.mod(message.author)
        admin = False
        master = False
    elif text.startswith("-a"):
        text = text.lstrip("-a").strip()
        mod = utils.mod(message.author)
        admin = utils.admin(message.author)
        master = False
    elif text.startswith("-*"):
        text = text.lstrip("-*").strip()
        mod = utils.mod(message.author)
        admin = utils.admin(message.author)
        master = utils.master(message.author)
    else:
        # If none of the filters is set use accordingly to normal permissions
        mod = utils.mod(message.author)
        admin = utils.admin(message.author)
        master = utils.master(message.author)
    # build a dict for all commands used later.
    help_dict = utils.build_help_dict(message, hidden, mod, admin, master)
    # If no hidden filter is set show all commands
    if text.lower() in ["", "-n", "-m", "-a"]:
        # all commands
        s = f"```fix\nPrefix: {prefix}```"
        c_list = []
        for MODULES, coms in help_dict.items():
            keys = [str(k) for k in coms.keys()]
            keys.sort()
            c_list.append("`" + str(MODULES) + "`: ```" + ", ".join(keys) + "```")
        c_list.sort()
        s += "".join(c_list)
        return s
    # If the filter is a module display the commands of this module
    elif text in help_dict.keys():
        # mods
        s = f"```fix\nModule: {text}\nPrefix: {prefix}```"
        c_list = []
        max_len = max([len(k) for k in help_dict[text].keys()])
        for k, v in help_dict[text].items():
            if v["usage"] == "":
                usage = ""
            else:
                usage = "\n    Usage:" + v["usage"]
            if len(v["alias"]) == 0:
                alias = ""
            elif len(v["alias"]) == 1:
                alias = "\n    Alias: " + v["alias"][0]
            else:
                alias = "\n    Aliases: " + ", ".join(v["alias"])
            c_list.append("`" + k.ljust(max_len) + "`: " + v["help"] + usage + alias)
        c_list.sort()
        s += " \n".join(c_list)
        return s
    # If the filter is not a module combine all commands that match part of the call, module or an alias
    else:
        s = "```md\nPrefix: " + prefix + "\nModule | command: help (usage)\n"
        c_list = []
        for k, v in commands.items():
            if text not in k and text not in v["module"] and all([text not in ali for ali in v["alias"]]):
                continue
            if v.get("forcehidden", False):
                continue
            if v["hidden"] and not hidden:
                continue
            if v["admin"] and not admin:
                continue
            if v["mod"] and not mod:
                continue
            if v["master"] and not master:
                continue
            if v["usage"] != "":
                usage = "\n    Usage: " + v["usage"]
            else:
                usage = ""
            if len(v["alias"]) == 0:
                alias = ""
            elif len(v["alias"]) == 1:
                alias = "\n    Alias: " + v["alias"][0]
            else:
                alias = "\n    Aliases: " + ", ".join(v["alias"])
            c_list.append("{module} | {cmd}: {help}".format(module=v["module"], cmd=k, help=v["help"]) + usage + alias)
        if len(c_list) == 0:
            return "No commands/modules found matching the current filter"
        else:
            # Sort them for neater display
            c_list.sort()
            s += "\n".join(c_list)
            s += "```"
            return s


# Run the bot
client.run(open("data/login").read().strip(), bot=(not selfbot))
