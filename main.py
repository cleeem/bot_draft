from genericpath import exists
from random import shuffle
from turtle import title
from discord import *
import discord.ui as bt
from discord.ext import commands
from csv import reader
import os

client = Client()

intents = Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", description="Bot de clem#1777", intents=intents)

bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed_help = Embed(title="help", description=f"Here are the steps to setup this bot.\n\nFirst, you need to do this : \n!setup @the_role_to_ping #the_channel_to_react\nfor example\n!setup @draft #draft\n\nThen to start a Draft just do the !draft command to start a draft.", color=0x33CAFF)
    await ctx.send(embed = embed_help)


@bot.event
async def on_ready():
    print("Ready !")
    activity = Game(name="!help", type=1)
    await bot.change_presence(status=Status.online, activity=activity)


def addincsv(url_file, objet, newline=True, delimiter=None):
    csv = open(url_file, 'a', encoding='utf-8')
    if newline:
        csv.write((str(objet)+'\n'))
    else:
        csv.write(str(objet))
        csv.write(str(delimiter))
    csv.close()


@bot.command()
async def setup(ctx, role_ping:Role):
    
    guild_id = ctx.guild.id

    if not exists(f"data/{guild_id}.csv"):
        channels = await create_channels(ctx)
        cate = channels[0]
        channel_ping = channels[1]
        channel_role = channels[2]
        addincsv(f"data/{guild_id}.csv", [role_ping.id, channel_ping.id])
        await ctx.send("setings registered")
        await create_role_channel(ctx=ctx, role_ping=role_ping, cate=cate, channel_draft=channel_ping, channel_role=channel_role)

    else:
        embed = Embed(description=f"You already setup your pings, would you like to change?", color=0x33CAFF)
        message_setup = await ctx.send(embed = embed)
        await message_setup.add_reaction("✅")
        await message_setup.add_reaction("⭕")

        def checkEmoji(reaction, user):
            return message_setup.id == reaction.message.id and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "⭕")
        
        reaction, user = await bot.wait_for("reaction_add", timeout = 9999, check = checkEmoji)

        if reaction.emoji == "✅":
            os.remove(f"data/{guild_id}.csv")
            addincsv(f"data/{guild_id}.csv", [role_ping, channel_ping])

            embed = Embed(description=f"updated role and channel", color=0x33CAFF)
            await message_setup.edit(embed=embed)
        if reaction.emoji == "⭕":
            await message_setup.delete()
            

async def create_channels(ctx):
    server = ctx.guild
    cate = await server.create_category(name="Draft")
    channel_role = await server.create_text_channel(name="Role", category=cate)
    channel_draft = await server.create_text_channel(name="Draft", category=cate)
    channel_start_draft = await server.create_text_channel(name="Start-Draft", category=cate)

    return cate, channel_draft, channel_role


async def create_role_channel(ctx, role_ping:Role, cate, channel_draft, channel_role):
    server : Guild = ctx.guild
    
    embed = Embed(title="Role Draft", description=f"To get {role_ping.mention}, react with the reaction below")
    mes = await channel_role.send(embed=embed)
    await mes.pin()
    # async def callback_role(interaction):
    #     await interaction.user.add_roles(role_ping)

    # async def callback_suppr(interaction):
    #     try:
    #         await interaction.user.remove_roles(role_ping)
    #     except:
    #         pass 

    # button_role = bt.Button(label="Draft Role", style=ButtonStyle.primary)
    # button_role.callback = callback_role

    # button_role_suppr = bt.Button(label="Draft Role", style=ButtonStyle.red)
    # button_role_suppr.callback = callback_suppr

    # view = bt.View()
    # view.add_item(button_role)
    # view.add_item(button_role_suppr)

    # message_react : channel = await channel_role.send(view=view, embed=embed)

@bot.command()
async def get_role(ctx):
    fichier = reader(open(f"data/{ctx.guild.id}.csv"))
    for ligne in fichier:
        role_ping = ligne[0].replace("[","").replace("'","")
    
    for role in ctx.guild.roles:
        if str(role.id) == str(role_ping):
            role_ping = role
            break
    
    present = False

    for role in ctx.author.roles:
        if role.id == role_ping.id:
            present=True
            break

    if present:
        await ctx.author.remove_roles(role_ping)
    else:
        await ctx.author.add_roles(role_ping)
        
    await ctx.message.delete()
    

@bot.command()
async def draft(ctx, nb_player=8):
    l=[2,4,6,8]
    if not nb_player in l:
        nb_player=8

    fichier = reader(open(f"data/{ctx.guild.id}.csv"))
    
    
    role_ping = None
    channel_ping = None

    for ligne in fichier:
        role_ping = ligne[0].replace("[","").replace("'","")
        channel_ping = ligne[1].replace("]","").replace("'","").replace("<","").replace(">","").replace("#","")

    send_channel_ping = bot.get_channel(int(channel_ping))

    membre : Member = ctx.author

    await send_channel_ping.send(f"<@&{role_ping}> a draft is starting... \nPlease react to the message bellow with ✅ to enter and with ⭕ to leave")
    

    embed = Embed(title="Draft", description=f"Players 0/{nb_player} :", color=0x33CAFF)
    embed.set_footer(text=f"draft started by {membre.name}#{membre.discriminator}")

    liste=[]


    async def callback_join(interaction):
        has_role=False
        for role in interaction.user.roles:
            if str(role.id) == str(role_ping):
                has_role=True
                break

        if (interaction.user.id not in liste) and has_role:
            liste.append(interaction.user.id)
            
            res = f"Players {len(liste)}/{nb_player} :\n"

            for player in liste:
                res = f"{res}-{bot.get_user(player).mention}\n"

            embed = Embed(title="Draft", description=res, color=0x33CAFF)
            embed.set_footer(text=f"draft started by {membre.name}#{membre.discriminator}")

            await interaction.message.edit(embed = embed)

            if len(liste) == nb_player:
                await message_all(ctx=ctx, membre=membre, message_start=message_start, send_channel_ping=send_channel_ping, liste=liste, nb_player=nb_player)

    async def callback_leave(interaction):
        if interaction.user.id in liste:
            liste.remove(interaction.user.id)
            res = f"Players {len(liste)}/{nb_player} :\n"

            for player in liste:
                res = f"{res}-{bot.get_user(player).mention}\n"

            embed = Embed(title="Draft", description=res, color=0x33CAFF)
            embed.set_footer(text=f"draft started by {membre.name}#{membre.discriminator}")

            await interaction.message.edit(embed = embed)        


    button_join = bt.Button(label="Join Draft", style=ButtonStyle.green)
    button_join.callback = callback_join

    button_leave = bt.Button(label="Leave Draft", style=ButtonStyle.danger)
    button_leave.callback = callback_leave

    view = bt.View()
    view.add_item(button_join)
    view.add_item(button_leave)

    message_start = await send_channel_ping.send(view=view, embed=embed)

async def message_all(ctx,message_start, send_channel_ping, membre, liste, nb_player):
        
    res = f"DRAFT ready\nPlayers :\n"

    for joueur in liste:
        player = bot.get_user(joueur)
        res = f"{res}-{player.mention}\n"
        try:
            await player.send(f"draft is starting")
        except:
            pass

    embed = Embed(title="Draft", description=res, color=0x33CAFF)
    embed.set_footer(text=f"draft started by {membre.name}#{membre.discriminator}")

    await message_start.edit(embed = embed)

    shuffle(liste)
    
    team_1 = ""
    team_2 = ""
    

    for i,joueur in enumerate(liste):
        player = bot.get_user(joueur)
        if i < int(nb_player/2):
            team_1 = f"{player.mention}\n{team_1}"
        else:
            team_2 = f"{player.mention}\n{team_2}"


    embed = Embed(title="Draft", description=res, color=0x33CAFF)
    await message_start.edit(embed = embed)
    await message_start.clear_reactions()

    embed = Embed(title="Draft", description=f"{team_1}🆚\n{team_2} \n\nPlease report the score using buttons below (all players must react), if both teams have the same amount of vote it will count as a loose for both team", color=0x33CAFF)
    embed.set_footer(text=f"draft started by {membre.name}#{membre.discriminator}")
    
    liste_score =  [0, 0]

    liste_vote = []

    async def callback_team_1(interaction):
        if interaction.user.id in liste:
            if not interaction.user.id in liste_vote:
                liste_vote.append(interaction.user.id)
                liste_score[0] += 1
                embed = Embed(title="Draft", description=f"{team_1}🆚\n{team_2} \n\nScore reported : {len(liste_vote)}/{nb_player}\nCurrent score, team 1 {liste_score[0]} | team 2 {liste_score[1]} \n\nPlease report the score using buttons below (all players must react), if both teams have the same amount of vote it will count as a loose for both team", color=0x33CAFF)

                await message_fin.edit(embed=embed)
    
    async def callback_team_2(interaction):
        if interaction.user.id in liste:
            if not interaction.user.id in liste_vote:
                liste_vote.append(interaction.user.id)
                liste_score[1] += 1
                embed = Embed(title="Draft", description=f"{team_1}🆚\n{team_2} \n\nScore reported : {len(liste_vote)}/{nb_player}\nCurrent score, team 1 {liste_score[0]} | team 2 {liste_score[1]} \n\nPlease report the score using buttons below (all players must react), if both teams have the same amount of vote it will count as a loose for both team", color=0x33CAFF)

                await message_fin.edit(embed=embed)
    button_team_1 = bt.Button(label="Team 1", style=ButtonStyle.primary)
    button_team_1.callback = callback_team_1

    button_team_2 = bt.Button(label="Team 2", style=ButtonStyle.primary)
    button_team_2.callback = callback_team_2

    view = bt.View()
    view.add_item(button_team_1)
    view.add_item(button_team_2)
    
    message_fin = await send_channel_ping.send(view=view, embed=embed)
    

import sys

try:
    sys.path.append("/python/token")
    import token_bot
except:
    sys.path.append("/home/cleeem/python/token")
    import token_bot
    
token_run = token_bot.tokens["token_bot_draft"]

bot.run(token_run)