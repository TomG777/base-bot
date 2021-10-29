import discord
from collections import defaultdict
from cmds import cmd

events = defaultdict(dict)
channel_events = defaultdict(dict)


def event(event_name: str):
    def _(fn):
        events[event_name][fn.__module__ + fn.__name__] = fn
        return fn

    return _


def channel_event(channel: int):
    def _(fn):
        channel_events[channel][fn.__module__ + fn.__name__] = fn
        return fn

    return _


@cmd("eventprint", forcehidden=True, master=True)
async def command_eventprint(**_):
    print(events)


@cmd("eventlist", forcehidden=True, master=True)
async def command_eventstats(**_):
    embed: discord.Embed = discord.Embed(name="Registered events")
    for k, v in events.items():
        embed.add_field(name=k, value=str(len(v)))
