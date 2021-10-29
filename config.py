import json

from cmds import cmd

Config_File = "data/config.json"

with open(Config_File) as jsondata:
    config = json.load(jsondata)
    jsondata.close()


def config_reload():
    global config
    with open(Config_File) as json_data:
        config = json.load(json_data)
        json_data.close()


def write_data(data):
    with open(Config_File, 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=2)


@cmd("configreload", __name__, help="Reload the config", admin=True)
async def command_configreload(**_):
    config_reload()
    return "Reloaded config"


@cmd("configsave", __name__, help="Save the config to file", master=True, hidden=True)
async def command_configsave(**_):
    write_data(config)
    return "Config saved"


@cmd("configraw", __name__, help="Show raw config", master=True, hidden=True)
async def command_config(**_):
    return str(config)


@cmd("config", __name__, help="Show raw config", master=True, hidden=True)
async def command_config(**_):
    return "```" + json.dumps(config, sort_keys=True, indent=2) + "```"


@cmd("configget", __name__, help="Show raw config key", master=True, hidden=True)
async def command_config(text, **_):
    return "```" + json.dumps(config.get(text, {}), sort_keys=True, indent=2) + "```"


@cmd("setconfigstr", __name__, help="Edit config file with string", usage="<key> <value>", master=True, hidden=True)
async def command_setconfigstr(text, **_):
    global config
    key, value = text.split(None, 1)
    config[key] = value
    write_data(config)
    return f"Config for {key} set to {str(value)}"


@cmd("setconfigfl", __name__, help="Edit config file with a float", usage="<key> <value>", master=True, hidden=True)
async def command_setconfigstr(text, **_):
    global config
    key, value = text.split(None, 1)
    try:
        value = float(value)
    except ValueError:
        return "Given value is not a float"
    config[key] = value
    write_data(config)
    return f"Config for {key} set to {str(value)}"


@cmd("setconfigint", __name__, help="Edit config file with an integer", usage="<key> <value>", admin=True, hidden=True)
async def command_setconfigint(text, **_):
    global config
    key, value = text.split(None, 1)
    try:
        value = int(value)
    except ValueError:
        return "Given value is not an integer"
    config[key] = value
    write_data(config)
    return f"Config for {key} set to {str(value)}"


@cmd("setconfigbool", __name__, help="Edit config file with a bool", usage="<key> <value>", master=True, hidden=True)
async def command_setconfigbool(text, **_):
    global config
    key, value = text.split(None, 1)
    if value.lower() in ["true", "t", "tr", "tru"]:
        value = True
    elif value.lower() in ["false", "f", "fal", "fals", "fa"]:
        value = False
    else:
        return "Given value is not a bool"
    config[key] = value
    write_data(config)
    return f"Config for {key} set to {str(value)}"


@cmd("setconfiglis", __name__, help="Edit config file with list", usage="<key> [<value1>\\n<value2>]", master=True,
     hidden=True)
async def command_setconfiglis(text, **_):
    global config
    key, value = text.split(None, 1)
    value = value.split("\n")
    config[key] = value
    write_data(config)
    return f"Config for {key} set to {str(value)}"


@cmd("setconfiglisapp", __name__, help="append value to config file with string", usage="<key> <value>", master=True,
     hidden=True)
async def command_setconfiglis(text, **_):
    global config
    key, value = text.split(None, 1)
    value = value.split("\n")
    for v in value:
        config[key].append(v)
    write_data(config)
    return f"Config for {key} appended with {str(value)}"
