import random
from typing import List
import discord
from discord.ext import commands


# Class that represents an initiative entry
class InitEntry:
    def __init__(self, name: str, roll: int, mod: int, owner: str, is_dead: bool = False, is_enemy: bool = False,
                 quantity: int = 1):
        self.roll = roll
        # A random decimal is added to the mod, to decide who goes first in a roll/mod tie
        self.mod = mod + random.randrange(0, 99) / 100
        self.name = name
        self.owner = owner
        self.quantity = quantity
        self.is_enemy = is_enemy
        self.is_dead = is_dead

        self.current_quantity = quantity

    def __str__(self):
        if self.quantity > 1:

            if self.current_quantity < self.quantity and not self.is_dead:
                quantity_string = f"(~~{self.quantity}~~ {self.current_quantity})"
            else:
                quantity_string = f"({self.quantity})"
        else:
            quantity_string = ""

        base_string = f"{self.name} {quantity_string}: {self.roll}"

        if self.is_enemy:
            base_string = "**" + base_string + "**"

        if self.is_dead:
            base_string = "~~" + base_string + "~~"

        return base_string


# Class that holds basic info
class BotInfo:
    def __init__(self):
        self.channel = None
        self.message = None
        self.position = -1
        self.mention = None


# Class that holds information about characters
class Character:
    def __init__(self, name: str, mod: int, adv: bool):
        self.name = name
        self.mod = mod
        self.adv = adv

    async def roll_character(self, ctx):
        if self.adv:
            await rolladv(ctx, self.name, self.mod)
        else:
            await roll(ctx, self.name, self.mod)


# Discord bot things
description = '''A bot to help manage initiative rolls for Dungeons and Dragons. Use ?help for commands'''
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='?', description=description, intents=intents)

init_entries_list = []
character_list = []

# Holds the (channel, message, position, mention message)  that is used to convey things
# Probably terrible practice, but idc
info = BotInfo()


# Returns true if init2 goes before init1
def lower_initiative(init1: InitEntry, init2: InitEntry):
    if init1.roll == init2.roll:
        return init1.mod < init2.mod
    return init1.roll < init2.roll


# Sorts a list of InitEntries by who would go first
def sort_entries(entries: List[InitEntry]):
    # Bubble sort bc who cares
    for _ in range(len(entries) - 1):
        for j in range(len(entries) - 1):
            if lower_initiative(entries[j], entries[j + 1]):
                holder = entries[j + 1]
                entries[j + 1] = entries[j]
                entries[j] = holder
    return entries


def set_up_character_list(charfile: str = ""):
    if len(charfile) == 0:
        return
    
    f = open(charfile, "r")
    content = f.readlines()
    for character in content:
        sets = character.split(" ")
        character_list.append(Character(sets[0].replace("_", " "), int(sets[1]), sets[2] == 't'))
    f.close()


async def index_display(ctx):
    await reprint()
    info.mention = await ctx.send(init_entries_list[info.position].owner + ", it is your turn to move " +
                                  init_entries_list[info.position].name + "!")


# Edits the ?set message
async def reprint():
    await info.message.edit(content=get_init_string())


# Returns the FULL initiative order in string form, with formatting and all
def get_init_string():
    init_string = ""
    count = 1
    for string_entry in sort_entries(init_entries_list):
        init_string += str(count) + ". " + str(string_entry)
        if info.position == count - 1:
            init_string += " <<<"
        count += 1
        init_string += "\n"

    return "**Initiative Order**\n\n" + init_string


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def set(ctx):
    """Sets this chat to be the current one used by the bot"""
    init_message = await ctx.send("**Initiative Order**\n\n")
    info.channel = init_message.channel
    info.message = init_message
    info.position = 0
    await reprint()


@bot.command()
async def add(ctx, name: str, roll: int, mod: int, quantity: int = 1):
    """Adds a person to initiative"""
    init_entries_list.append(InitEntry(name.replace("_", " "), roll, mod, ctx.author.mention, quantity=quantity,
                                       is_enemy=not isinstance(ctx.channel, discord.TextChannel)))
    await reprint()


@bot.command()
async def roll(ctx, name: str, mod: int, quantity: int = 1):
    """Rolls an initiative entry with the given init mod and adds them to initiative"""
    await add(ctx, name, random.randint(1, 20), mod, quantity)


@bot.command()
async def rolladv(ctx, name: str, mod: int, quantity: int = 1):
    """Rolls an initiative entry with the given init mod and advantage and adds them to initiative"""
    await add(ctx, name, max(random.randint(1, 20), random.randint(1, 20)), mod, quantity)


@bot.command()
async def rollchar(ctx, name: str):
    """Rolls a character by name/nickname. For now, dm me directly if you want your character added."""
    try:
        character_list[[x.name for x in character_list].index(name)].roll(ctx)
    except AttributeError:
        pass


@bot.command()
async def kill(ctx, index: int, quantity: int = 1):
    """Kills some number of something, killing if it hits 0 or below"""
    try:
        entry = init_entries_list[index - 1]
        entry.current_quantity -= quantity
        if entry.current_quantity >= entry.quantity:
            entry.quantity = entry.current_quantity
        if entry.current_quantity <= 0:
            entry.is_dead = True
            entry.quantity = 0
    except IndexError:
        pass
    await reprint()


@bot.command()
async def unkill(ctx, index: int, quantity: int = 1):
    """Adds some number of something. Basically unkills it."""
    await kill(ctx, index, quantity * -1)


@bot.command()
async def clear(ctx):
    """Clears the initiative list"""
    init_entries_list.clear()
    await reprint()


@bot.command()
async def next(ctx):
    """Mentions the user who controls the character up next in initiative"""
    # Skip dead people
    orig = info.position
    while True:
        info.position += 1
        info.position %= len(init_entries_list)
        if info.position == orig or not init_entries_list[info.position].is_dead:
            break
    await index_display(ctx)


@bot.command()
async def jump(ctx, index: int):
    """Jumps to the specified index in initiative, mentioning the user there"""
    info.position = index - 1
    info.position %= len(init_entries_list)
    await index_display(ctx)


@bot.command()
async def remove(ctx, index: int):
    """Removes an entry at the given index"""
    try:
        del init_entries_list[index - 1]
    except IndexError:
        pass
    await reprint()


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if isinstance(message.channel, discord.TextChannel) and message.channel == info.channel:
        await message.delete()

set_up_character_list()
bot.run('<TOKEN>')
