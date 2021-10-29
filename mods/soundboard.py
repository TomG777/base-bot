import asyncio

import datetime
import discord
import pathlib
from urllib.parse import urlparse
import urllib.request
import urllib.error
import youtube_dl
import random

from cmds import cmd
from events import event
import utils

AUDIO_EXTENSIONS = ["mp3", "opus", "m4a", "custom", "wav"]
AUDIO_FILES = []
for extension in AUDIO_EXTENSIONS:
    AUDIO_FILES.extend([f for f in pathlib.Path("data/sounds/").rglob("*." + extension) if f.is_file()])
AUDIO_FILES.sort(key=lambda x: x.name.lower())


def update_files():
    global AUDIO_FILES
    AUDIO_FILES = []
    # noinspection PyShadowingNames
    for extension in AUDIO_EXTENSIONS:
        AUDIO_FILES.extend([f for f in pathlib.Path("data/sounds/").rglob("*." + extension) if f.is_file()])
    AUDIO_FILES.sort(key=lambda x: x.name.lower())


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class VoiceError(Exception):
    pass


@event("on_voice_state_update")
async def event_voice_state_update(member: discord.Member, client: discord.Client, before, after, **_):
    print("Hallo")
    if member.id is client.user.id:
        print("hoi")
        print(after)
        if after is None or after.channel is None:
            print("Doei")
            await asyncio.sleep(1)
            audit = False
            async for action in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect,
                                                        after=(datetime.datetime.utcnow() - datetime.timedelta(
                                                            seconds=20))):
                print("HENK!")
                print(action)
                action: discord.AuditLogEntry
                if action.created_at >= datetime.datetime.utcnow() - datetime.timedelta(seconds=20):
                    print(action.created_at)
                    print("Piet")
                    print(datetime.datetime.utcnow() - datetime.timedelta(seconds=20))
                    audit = True
                    break
            if audit:
                channel = before.channel
                await asyncio.sleep(random.randrange(0, 20))
                if not member.guild.voice_client:
                    await channel.connect()
    if not after or after.channel is None:
        voice = member.guild.voice_client
        if voice and len([m for m in voice.channel.members if not m.bot]) == 0:
            await voice.disconnect(force=True)
    elif before.channel and before.channel != after.channel:
        voice = member.guild.voice_client
        if voice and len([m for m in voice.channel.members if not m.bot]) == 0:
            await voice.disconnect(force=True)


async def get_voice(user: discord.Member, guild: discord.guild, connect: bool = True, join: bool = True):
    voice: discord.VoiceState = user.voice
    if not voice or not voice.channel:
        if utils.admin(user):
            if guild.voice_client:
                return guild.voice_client
        if connect:
            raise VoiceError("Error: You are required to be connected to a voice channel to use this command")
        else:
            return None
    else:
        voice_client: discord.VoiceClient = guild.voice_client
        if not voice_client:
            if connect:
                try:
                    vclient: discord.VoiceClient = await voice.channel.connect(timeout=10.0)
                    voice_client = vclient
                except asyncio.TimeoutError:
                    raise VoiceError("Error: Connecting to voice timed out")
                except discord.opus.OpusNotLoaded:
                    raise VoiceError("Error: Opus is not loaded, please get into contact with a maintainer of the bot.")
                except discord.Forbidden:
                    raise VoiceError("Error: I do not have permission to join your voice channel")
            else:
                return None
        else:
            if voice_client.channel.id is not voice.channel.id and join:
                try:
                    await voice_client.move_to(voice.channel)
                except discord.Forbidden:
                    raise VoiceError("Error: I do not have permission to join your voice channel")
        return voice_client


@cmd("leave", __name__, help="Stop the soundboard from playing")
async def command_leave(author: discord.Member, guild: discord.Guild, **_):
    voice: discord.VoiceState = author.voice
    if utils.mod(author):
        vclient = guild.voice_client
        if not vclient:
            return "Error: Not connected to a voice channel"
        if vclient.is_connected():
            await vclient.disconnect(force=True)
        return "Left the voice channel for this server"
    if not voice or not voice.channel:
        return "Error: You are required to be connected to a voice channel to use this command"
    else:
        vclient = guild.voice_client
        if not vclient:
            return "Error: Not connected to a voice channel"
        if vclient.is_connected():
            await vclient.disconnect(force=True)
        return "Left the voice channel for this server"


@cmd("list", __name__, help="List the files supported for the soundboard", usage="[filter]")
async def command_list(text, **_):
    if text:
        files = [file.name.rsplit(".", 1)[0] for file in AUDIO_FILES if text.lower() in file.name.lower()]
    else:
        files = [file.name.rsplit(".", 1)[0] for file in AUDIO_FILES]
    result = ", ".join(files)
    if len(result) > 1950:
        return "Too many files! please refine your search"
    return "Known files: ```\n" + result + "```"


@cmd("update", __name__, help="Update the list of music files", mod=True)
async def command_update(**_):
    update_files()
    return f"There are now {str(len(AUDIO_FILES))} sounds in the list"


@cmd("download", __name__, help="Download a new sound file", usage="<url> name", mod=True)
async def command_download(text, **_):
    url, name = text.split(None, 1)
    if not is_url(url):
        return f"Error: Malformed url `{url}`"
    elif "." in name:
        return "Error: Name is not allowed to contain a dot `.`"
    else:
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11")
            r = urllib.request.urlopen(req)
            with open(f"data/sounds/{name}.custom", "wb") as file:
                file.write(r.read())
                file.close()
            # urllib.request.urlretrieve(req, f"data/sounds/{name}.custom")
        except urllib.error.HTTPError as e:
            return "Error on file download:  " + str(e)
        update_files()
        return f"Downloaded sound: `{name}` from `{url}`"


async def play_sound(voice_client: discord.VoiceClient, file: pathlib.PurePath, message: discord.Message,
                     client: discord.Client):
    source: discord.FFmpegOpusAudio = await discord.FFmpegOpusAudio.from_probe(file)

    # noinspection PyUnusedLocal
    def finish(error):
        asyncio.run_coroutine_threadsafe(clear(), client.loop)

    async def clear():
        await message.clear_reaction("🔇")

    voice_client.stop()
    voice_client.play(source, after=finish)
    await message.add_reaction("🔇")

    # noinspection PyShadowingNames
    def check(reaction: discord.Reaction, user):
        return str(
            reaction.emoji) == '🔇' and reaction.message.id == message.id and user != client.user
        # and user == author

    try:
        await client.wait_for("reaction_add", timeout=60, check=check)
        voice_client.stop()
    except asyncio.TimeoutError:
        await message.clear_reaction("🔇")


async def play_link(voice_client: discord.VoiceClient, link: str, message: discord.Message, client: discord.Client,
                    volume: float = 0.4):
    ydl_opts = {
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128', }],
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0',
    }
    voice_client.stop()

    def finish(error):
        asyncio.run_coroutine_threadsafe(clear(), client.loop)

    async def clear():
        await message.clear_reaction("🔇")

    try:
        print(0)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.cache.remove()
            info_dict = ydl.extract_info(link, download=False)
            # print(info_dict)
            info = info_dict["formats"].pop()
            audio = discord.FFmpegPCMAudio(info["url"])
            volume = discord.PCMVolumeTransformer(audio, volume=volume)
            voice_client.play(volume, after=clear)
            await message.add_reaction("🔇")

            # noinspection PyShadowingNames
            def check(reaction: discord.Reaction, user):
                return str(
                    reaction.emoji) == '🔇' and reaction.message.id == message.id and user != client.user

            try:
                await client.wait_for("reaction_add", timeout=300, check=check)
                voice_client.stop()
            except asyncio.TimeoutError:
                await message.clear_reaction("🔇")

    except ValueError as e:
        print(e)
        return e


@cmd("play", __name__, help="Play a sound", usage="<sound>", private=False)
async def command_play(message: discord.Message, text: str, author: discord.Member, client: discord.Client,
                       guild: discord.Guild, **_):
    if text.startswith("-v "):
        vol, text = text.lstrip("-v ").split(None, 1)
        try:
            vol = float(vol.replace(",", "."))
        except ValueError:
            return "Error: invalid input"
    else:
        vol = 0.4
    if is_url(text):
        try:
            voice_client = await get_voice(author, guild)
            await play_link(voice_client, text, message, client, vol)
        except VoiceError as e:
            return str(e)
        return
    file: pathlib.PurePath
    try:
        file = next(file for file in AUDIO_FILES if file.name.lower().startswith(text.lower()))
    except StopIteration:
        try:
            file = next(file for file in AUDIO_FILES if text.lower() in file.name.lower())
        except StopIteration:
            return "Error: file not found, please check your search"
    try:
        voice_client = await get_voice(author, guild)
        await play_sound(voice_client, file, message, client)
    except VoiceError as e:
        return str(e)


@cmd("connect", __name__, help="Connect to your voice channel without playing a sound", private=False)
async def command_connect(author: discord.Member, guild: discord.Guild, **_):
    try:
        voice_client = get_voice(author, guild)
        if voice_client:
            return "Connected!"
        else:
            return "Error: something interesting happened. Please get in contact with a administrator."
    except VoiceError as e:
        return str(e)
