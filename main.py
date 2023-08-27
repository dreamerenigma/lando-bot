# -*- coding:utf-8 -*-
import discord
from discord.ext import commands
from config import DISCORD_TOKEN

import os
import time
import youtube_dl

from db import DataBase
from ban_words import *

db = DataBase('bot_db.db')

intents = discord.Intents.default().all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('Bot online!')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('/help'))

server, server_id, name_channel = None, None, None

domains = ['https://www.youtube.com/', 'http://www.youtube.com/', 'https://youtu.be/', 'http://youtu.be/']
async def check_domains(link):
    for x in domains:
        if link.startswith(x):
            return True
    return False

async def check_count(ctx):
    global db
    id = ctx.author.id
    sql = "SELECT counter FROM muted_users WHERE user_id = %d" % id
    result = db.select_with_fetchone(sql)
    if result is None:
        add_sql = "INSERT INTO muted_users VALUES (%d, 0, '%s')" % (id, time.ctime())
        db.query(add_sql)
        sql = "SELECT counter FROM muted_users WHERE user_id = %d" % id
        result = db.select_with_fetchone(sql)
    result = result[0]
    if result == 0:
        return 'delete', result
    elif result % 5 == 0:
        return 'mute', result
    else:
        return 'delete', result

async def add_role(ctx, *, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    author = ctx.author
    await discord.Member.add_roles(author, role)

async def user_mute(ctx):
    author = ctx.author
    await ctx.channel.purge(limit=1)
    await add_role(ctx, role_name='Muted')

# Issuing mute to users
@bot.event
async def on_message(ctx):
    author = ctx.author
    if ctx.author == bot.user:
        return
    print(ctx.content)
    for i in ban_words:
        if i in ctx.content.lower():
            response = await check_count(ctx)
            response_msg = response[0]
            response_counter = response[1]
            if response_msg == 'delete':
                await ctx.delete()
                await ctx.channel.send(f'{author.mention}, не используйте запрещенные слова!')
            else:
                await user_mute(ctx)
                await ctx.channel.send(f'{author.mention}, вам выдан мут, по вопросам к администрации!')
            response_counter += 1
            c_sql = "UPDATE muted_users SET counter = %d WHERE user_id = %d" % (response_counter, author.id)
            db.query(c_sql)
            return
    await bot.process_commands(ctx)

# Removing a stop word
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    msg = message.content.lower()

    if msg in ban_words:
        await message.delete()
        await message.author.send(f'{message.author.name}, не надо такое писать!')

# Clear message
@bot.command(pass_context=True)
async def clear(ctx, amount=100):
    """Удаляет сообщения"""
    await ctx.channel.purge(limit=amount)

# Clear command
# @bot.command(pass_context=True)
# async def del_command(ctx, amount=1):
#     """Удаляет команды"""
#     await ctx.channel.purge(limit=amount)
#
#     author = ctx.message.author
#     await ctx.send(f'Hello{author.mention}')

# User survey
@bot.command()
async def srv(ctx, *, command):
    """Делает быстрый опрос"""
    params = command.split('&')
    if len(params) == 2 or len(params) == 3:
        if len(params) == 3:
            title = params[2]
        else:
            title = ''
        text = params[0]
        if params[1] == '':
            color = 0x15e8c5
        else:
            color = params[1]
            try:
                color = int(color, 16)
            except:
                await ctx.channel.send(f'{ctx.author.mention}, цвет передан не верно!')
                return
    elif len(params) == 1:
        text = command
        color = 0x15e8c5
        title = ''
    else:
        await ctx.channel.send(f'{ctx.author.mention},  команда не корректна!')
    await ctx.message.delete()
    msg = await ctx.channel.send(embed=discord.Embed(title=title, description=text, color=color))
    emj = bot.get_emoji()
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')
    await msg.add_reaction(emj)

@bot.command()
async def emb(ctx, *, command):
    """Делает быстрый эмбед"""
    params = command.split('&')
    if len(params) == 2 or len(params) == 3:
        if len(params) == 3:
            title = params[2]
        else:
            title = ''
        text = params[0]
        if params[1] == '':
            color = 0x15e8c5
        else:
            color = params[1]
            try:
                color = int(color, 16)
            except:
                await ctx.channel.send(f'{ctx.author.mention}, цвет передан не верно!')
                return
    elif len(params) == 1:
        text = command
        color = 0x15e8c5
        title = ''
    else:
        await ctx.channel.send(f'{ctx.author.mention},  команда не корректна!')
    await ctx.message.delete()
    await ctx.channel.send(embed=discord.Embed(title=title, description=text, color=color))

# Turning on the music
@bot.command()
async def play(ctx, *, command=None):
    """Воспроизводит музыку"""
    global server, server_id, name_channel
    author = ctx.author
    if command == None:
        server = ctx.guild
        name_channel = author.voice.channel.name
        voice_channel = discord.utils.get(server.voice_channels, name=name_channel)
    params = command.split(' ')
    if len(params) == 1:
        source = params[0]
        server = ctx.guild
        name_channel = author.voice.channel.name
        voice_channel = discord.utils.get(server.voice_channels, name=name_channel)
        print('param 1')
    elif len(params) == 3:
        server_id = params[0]
        voice_id = params[1]
        source = params[2]
        try:
            server_id = int(server_id)
            voice_id = int(voice_id)
        except:
            await ctx.channel.send(f'{author.mention}, id сервера или войса должно быть целочисленным!')
            return
        print('param 3')
        server = bot.get_guild(server_id)
        voice_channel = discord.utils.get(server.voice_channels, id=voice_id)
    else:
        await ctx.channel.send(f'{author.mention} команда не корректна!')
        return

    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    if source == None:
        pass
    elif source.startswith('http'):
        if not await check_domains(source):
            await ctx.channel.send(f'{author.mention}, ссылка не является разрешенной!')
            return
        song_there = os.path.isfile('song.mp3')
        try:
            if song_there:
                os.remove('song.mp3')
        except PermissionError:
            await ctx.channel.send('Недостаточно прав для удаления файла!')
            return
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([source])
        for file in os.listdir('./'):
            if file.endswith('.mp3'):
                os.rename(file, 'song.mp3')
        voice.play(discord.FFmpegPCMAudio('song.mp3'))

    else:
        voice.play(discord.FFmpegPCMAudio(f'{source}'))

@bot.command()
async def leave(ctx):
    """Командует боту выйти из войса"""
    global server, name_channel
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, бот уже отключен от войса!')

@bot.command()
async def pause(ctx):
    """Ставит музыку на паузу"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, Музыка не воспроизводится!')

@bot.command()
async def resume(ctx):
    """Снимает музыку с паузы"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, Музыка уже играет!')

@bot.command()
async def stop(ctx):
    """Прекращает воспроизвение музыки"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    voice.stop()

bot.run(DISCORD_TOKEN)