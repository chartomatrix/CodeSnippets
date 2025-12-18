import discord
from discord.ext import commands
from discord import app_commands
import json
import os

tkn = ""
cfil = "configs.json"
cfgs = {}

def ldcfg():
    global cfgs
    try:
        if os.path.exists(cfil):
            with open(cfil, 'r') as f:
                cfgs = json.load(f)
    except:
        cfgs = {}

def svcfg():
    try:
        with open(cfil, 'w') as f:
            json.dump(cfgs, f, indent=2)
    except:
        pass

class SBot(commands.Bot):
    def __init__(self):
        ints = discord.Intents.default()
        ints.message_content = True
        ints.reactions = True
        super().__init__(command_prefix='!', intents=ints)
        
    async def setup_hook(self):
        ldcfg()
        await self.tree.sync()
    
    async def on_ready(self):
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="suggestions"))
    
    async def on_guild_join(self, gld):
        ch = None
        for c in gld.text_channels:
            if c.name.lower() in ['general', 'welcome', 'bot-commands'] and c.permissions_for(gld.me).send_messages:
                ch = c
                break
        
        if not ch:
            for c in gld.text_channels:
                if c.permissions_for(gld.me).send_messages:
                    ch = c
                    break
        
        if ch:
            emb = discord.Embed(title="Thanks!", description="I manage suggestions.", color=discord.Color.blue())
            emb.add_field(name="Setup", value="Use `/setup`", inline=False)
            try:
                await ch.send(embed=emb)
            except:
                pass

bot = SBot()

def gtcfg(gid):
    gs = str(gid)
    if gs not in cfgs:
        cfgs[gs] = {'sgch': None, 'apch': None, 'ftch': None, 'thr': 5, 'sent': []}
    
    if 'sent' not in cfgs[gs]: cfgs[gs]['sent'] = []
    return cfgs[gs]

def svgld(gid, c):
    cfgs[str(gid)] = c
    svcfg()

@bot.tree.command(name="setup", description="Setup channels")
async def setup(intr, sgch: discord.TextChannel, apch: discord.TextChannel, ftch: discord.TextChannel, thr: int = 5):
    if not (intr.user.guild_permissions.manage_guild or intr.user.id == intr.guild.owner_id):
        await intr.response.send_message("No perms", ephemeral=True)
        return
    
    if thr < 1:
        await intr.response.send_message("Bad threshold", ephemeral=True)
        return
    
    c = gtcfg(intr.guild.id)
    c['sgch'] = sgch.id
    c['apch'] = apch.id
    c['ftch'] = ftch.id
    c['thr'] = thr
    svgld(intr.guild.id, c)

    emb = discord.Embed(title="Done", color=discord.Color.green())
    await intr.response.send_message(embed=emb)

@bot.tree.command(name="set_threshold", description="Set threshold")
async def stthr(intr, amt: int):
    if not intr.user.guild_permissions.administrator:
        await intr.response.send_message("Admin only", ephemeral=True)
        return
    
    c = gtcfg(intr.guild.id)
    c['thr'] = amt
    svgld(intr.guild.id, c)
    await intr.response.send_message(f"Threshold: {amt}")

@bot.tree.command(name="view_config", description="View config")
async def vwcfg(intr):
    c = gtcfg(intr.guild.id)
    s = f"<#{c['sgch']}>" if c['sgch'] else "None"
    a = f"<#{c['apch']}>" if c['apch'] else "None"
    f = f"<#{c['ftch']}>" if c['ftch'] else "None"
    
    emb = discord.Embed(title="Config", color=discord.Color.blue())
    emb.add_field(name="Suggestion", value=s)
    emb.add_field(name="Approval", value=a)
    emb.add_field(name="Featured", value=f)
    emb.add_field(name="Threshold", value=str(c['thr']))
    await intr.response.send_message(embed=emb)

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    c = gtcfg(msg.guild.id)
    if msg.channel.id == c['sgch']:
        await msg.add_reaction('👍')
        await msg.add_reaction('👎')

@bot.event
async def on_reaction_add(r, u):
    if u.bot: return
    c = gtcfg(r.message.guild.id)
    if r.message.channel.id != c['sgch']: return
    if r.message.id in c['sent']: return
    if str(r.emoji) != '👍': return
    
    up = 0
    down = 0
    for x in r.message.reactions:
        if str(x.emoji) == '👍': up = x.count
        elif str(x.emoji) == '👎': down = x.count
    
    if up >= c['thr'] and up >= down:
        c['sent'].append(r.message.id)
        svgld(r.message.guild.id, c)
        await sndapp(r.message, c)

async def sndapp(msg, c):
    ch = bot.get_channel(c['apch'])
    if not ch: return
    
    emb = discord.Embed(description=msg.content, color=discord.Color.orange())
    emb.set_author(name=msg.author.display_name, icon_url=msg.author.display_avatar.url)
    
    v = AppView(msg, c)
    await ch.send(embed=emb, view=v)

class AppView(discord.ui.View):
    def __init__(self, msg, c):
        super().__init__(timeout=None)
        self.msg = msg
        self.c = c
    
    @discord.ui.button(label='Approve', style=discord.ButtonStyle.green)
    async def app(self, intr, btn):
        if not intr.user.guild_permissions.manage_messages: return
        await intr.response.send_modal(AppMod(self.msg, self.c, intr.message))
    
    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red)
    async def dny(self, intr, btn):
        if not intr.user.guild_permissions.manage_messages: return
        emb = intr.message.embeds[0]
        emb.color = discord.Color.red()
        emb.title = "Denied"
        for x in self.children: x.disabled = True
        await intr.response.edit_message(embed=emb, view=self)

class AppMod(discord.ui.Modal, title='Approve'):
    def __init__(self, msg, c, amsg):
        super().__init__()
        self.msg = msg
        self.c = c
        self.amsg = amsg

    note = discord.ui.TextInput(label='Note', required=False)

    async def on_submit(self, intr):
        ch = bot.get_channel(self.c['ftch'])
        if ch:
            emb = discord.Embed(description=self.msg.content, color=discord.Color.gold())
            emb.set_author(name=self.msg.author.display_name, icon_url=self.msg.author.display_avatar.url)
            if self.note.value: emb.add_field(name="Note", value=self.note.value)
            
            m = await ch.send(embed=emb)
            try:
                await m.create_thread(name="Discussion")
            except: pass
        
        try:
            dm = discord.Embed(title="Approved!", description=f"Server: {intr.guild.name}", color=discord.Color.green())
            if self.note.value: dm.add_field(name="Note", value=self.note.value)
            await self.msg.author.send(embed=dm)
        except: pass
        
        emb = self.amsg.embeds[0]
        emb.title = "Approved"
        emb.color = discord.Color.green()
        v = discord.ui.View()
        v.add_item(discord.ui.Button(label='Approved', disabled=True))
        await intr.response.edit_message(embed=emb, view=v)

if __name__ == "__main__":
    bot.run(tkn)
