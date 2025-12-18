import discord
from discord.ext import commands
import re
import aiohttp
import asyncio
import json
import os

tkn = ""
cfil = "config.json"

def ldcfg():
    if os.path.exists(cfil):
        try:
            with open(cfil, 'r') as f:
                return set(json.load(f).get('active_guilds', []))
        except:
            return set()
    svcfg(set())
    return set()

def svcfg(g):
    try:
        with open(cfil, 'w') as f:
            json.dump({'active_guilds': list(g)}, f, indent=2)
    except:
        pass

ints = discord.Intents.default()
ints.message_content = True
bot = commands.Bot(command_prefix='!', intents=ints)
glds = ldcfg()

kws = [
    'adult', 'sex', 'porn', 'xxx', 'nsfw', 'nude', 'naked', 'erotic', 'sexy', 'hot',
    'kinky', 'fetish', 'bdsm', 'kink', 'horny', 'sexual', 'seduction', 'intimate',
    'sensual', 'pleasure', 'desire', 'lust', 'passion', 'naughty', 'dirty',
    'boobs', 'tits', 'ass', 'pussy', 'dick', 'cock', 'penis', 'vagina', 'breast',
    'nipple', 'butt', 'booty', 'thigh', 'curves', 'body', 'naked body',
    'hookup', 'dating', 'meet', 'chat', 'cam', 'webcam', 'strip', 'masturbate',
    'orgasm', 'climax', 'cumming', 'squirt', 'moan', 'seduce', 'flirt',
    '18+', '21+', 'adults only', 'mature', 'age verified', 'legal age',
    'onlyfans', 'premium', 'exclusive', 'private', 'vip', 'leaks', 'leaked',
    'content', 'pics', 'videos', 'media', 'gallery', 'collection',
    'fuck', 'fucking', 'bang', 'smash', 'breed', 'daddy', 'mommy', 'sugar',
    'escort', 'prostitute', 'whore', 'slut', 'bitch', 'hoe',
    'singles', 'lonely', 'horny girls', 'hot girls', 'cute girls', 'teens',
    'milf', 'cougar', 'sugar daddy', 'sugar baby', 'relationship', 'romance',
    'strip club', 'cam girl', 'cam boy', 'model', 'amateur', 'professional',
    'uncensored', 'explicit', 'graphic', 'hardcore', 'softcore', 'rated r',
    'x-rated', 'adult entertainment', 'adult content'
]

def mkpat():
    pats = []
    lm = {'a': '[a@4]', 'e': '[e3]', 'i': '[i1!]', 'o': '[o0]', 's': '[s$5]', 'l': '[l1!]', 't': '[t7]'}
    for kw in kws:
        esc = re.escape(kw)
        sub = ''.join(lm.get(c.lower(), re.escape(c)) for c in kw)
        pats.extend([fr'\b{esc}\b', fr'\b{sub}\b'])
    return '|'.join(f'({p})' for p in pats)

pat = mkpat()

invpats = [
    r'(?:https?://)?(?:www\.)?discord\.(?:gg|io|me|li)/[a-zA-Z0-9]+',
    r'(?:https?://)?(?:www\.)?discord\.com/invite/[a-zA-Z0-9]+',
    r'(?:https?://)?(?:www\.)?discordapp\.com/invite/[a-zA-Z0-9]+',
    r'discord\.gg/[a-zA-Z0-9]+',
    r'discord\.io/[a-zA-Z0-9]+',
    r'discord\.me/[a-zA-Z0-9]+',
    r'discord\.li/[a-zA-Z0-9]+',
]

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="invites"))
    try:
        await bot.tree.sync()
    except:
        pass

@bot.tree.command(name="activate", description="Activate NSFW filtering")
async def act(intr):
    if not (intr.user.guild_permissions.manage_guild or intr.user.id == intr.guild.owner_id):
        await intr.response.send_message("No perms", ephemeral=True)
        return
    
    gid = intr.guild.id
    if gid in glds:
        await intr.response.send_message("Already active", ephemeral=True)
    else:
        glds.add(gid)
        svcfg(glds)
        await intr.response.send_message("Activated", ephemeral=True)

@bot.tree.command(name="deactivate", description="Deactivate NSFW filtering")
async def deact(intr):
    if not (intr.user.guild_permissions.manage_guild or intr.user.id == intr.guild.owner_id):
        await intr.response.send_message("No perms", ephemeral=True)
        return
    
    gid = intr.guild.id
    if gid not in glds:
        await intr.response.send_message("Not active", ephemeral=True)
    else:
        glds.remove(gid)
        svcfg(glds)
        await intr.response.send_message("Deactivated", ephemeral=True)

@bot.tree.command(name="status", description="Check status")
async def st(intr):
    active = intr.guild.id in glds
    await intr.response.send_message(f"{'Active' if active else 'Inactive'}", ephemeral=True)

async def gtinv(code):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://discord.com/api/v10/invites/{code}") as r:
                if r.status == 200:
                    return (await r.json()).get('guild', {}).get('name', '')
    except:
        pass
    return None

def excodes(txt):
    codes = []
    for p in invpats:
        for m in re.findall(p, txt, re.IGNORECASE):
            c = m.split('/')[-1]
            if c and len(c) >= 3:
                codes.append(c)
    return codes

def isnsfw(nm):
    if not nm: return False
    return bool(re.search(pat, nm, re.IGNORECASE))

@bot.event
async def on_message(msg):
    if msg.author.bot or not msg.guild: return
    if msg.guild.id not in glds: return
    
    codes = excodes(msg.content)
    if codes:
        for c in codes:
            nm = await gtinv(c)
            if nm and isnsfw(nm):
                try:
                    await msg.delete()
                    w = await msg.channel.send(f"**{msg.author.mention}**, NSFW invite deleted.\nServer: `{nm}`")
                    await asyncio.sleep(5)
                    try: await w.delete()
                    except: pass
                    break
                except:
                    pass

if __name__ == "__main__":
    bot.run(tkn)
