from typing import Callable, Tuple, List
commands = {}


def cmd(name: str, module: str = "Default", alias: Tuple = tuple(), hiddenalias: Tuple = tuple(), master: bool = False,
        admin: bool = False, mod: bool = False, alt_roles: List = [], mod_overwrite: bool = False, help: str = "", usage: str = "", privateonly: bool = False,
        private: bool = True, guilds: List = [], guilds_blacklist: List = [], hidden: bool = False, forcehidden: bool = False, bots: bool = False) -> Callable:
    """Construction for commands, when used they will be added to a dictionary which will check for them inside messages

    :return: Callable
    :rtype: Callable
    :param name: The name/what is called to run the command
    :param module: The name of which this module this command is part of
    :param alias: A tuple of aliases that are alternative calls to the command
    :param hiddenalias: Same as alias but will not turn up in the help command
    :param master: Only a master (utils.master()) will be able to use this command
    :param admin: Only an admin (utils.admin()) will be able to use this command
    :param mod: Only a mod (utils.mod()) will be able to use this command
    :param alt_roles: Only people with this role(id) will be able to use this command
    :param mod_overwrite: for previous parameter allow people with proper staff check also access
    :param help: The help description of what this command does
    :param usage: Optional string declaring the arguments
    :param privateonly: If the command can only be used in private chat
    :param guilds: If set list of guilds this command can be used in
    :param guilds_blacklist: If set blacklist of guilds this command can not be used in
    :param private: If the command is allowed in private chat
    :param hidden: If the command is hidden from the help command (can be revealed with -h option
    :param forcehidden: If the command is hidden, prevents -h option
    :param bots: If bots can use this command
    """
    def _(fn):
        modu = module
        while modu.startswith("mods."):
            modu = modu[5:]
        commands[name] = {
            "f": fn,  # Functon itself
            "module": modu,  # Module the command is part of
            "alias": alias,  # List of aliases for the command
            "hiddenalias": hiddenalias,  # List of aliases not to display in help command
            "master": master,  # If command can only be used by a master
            "admin": admin,  # If command can only be used by an admin
            "mod": mod,  # if command can only be used by a mod
            "alt_roles": alt_roles,  # list of roles to limit access to
            "mod_overwrite": mod_overwrite,  # when a role set allow access to staff check
            "help": help,  # explaination of the command
            "usage": usage,  # display of arguments
            "privateOnly": privateonly,  # If command can only be used in private channe;
            "private": private,  # if command is allowed to be used in private channel
            "guilds": guilds,  # If set list of guilds this command can be used in
            "guilds_blacklist": guilds_blacklist,  # If set blacklist of guilds this command can not be used in
            "hidden": hidden,  # if command is hidden from help command
            "forcehidden": forcehidden,  # if command is hidden from help command
            "bots": bots  # if bots can use the command
        }
        return fn

    return _
