import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import sqlite3

tkn = ""

def initdb():
    cn = sqlite3.connect('games.db')
    c = cn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS game_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, guild_id INTEGER,
        game_type TEXT, result TEXT, timestamp TEXT, points_earned INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_points (
        user_id INTEGER PRIMARY KEY, guild_id INTEGER, total_points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, draws INTEGER DEFAULT 0)''')
    cn.commit()
    cn.close()

class GBot(commands.Bot):
    def __init__(self):
        ints = discord.Intents.default()
        ints.message_content = True
        super().__init__(command_prefix='!', intents=ints)
        self.games = {}
        
    async def setup_hook(self):
        initdb()
        await self.tree.sync()
    
    async def on_ready(self):
        await self.change_presence(activity=discord.Game("Games"))

bot = GBot()

def addpts(uid, gid, pts, res):
    cn = sqlite3.connect('games.db')
    c = cn.cursor()
    c.execute('INSERT OR IGNORE INTO user_points (user_id, guild_id, total_points, level, wins, losses, draws) VALUES (?, ?, 0, 1, 0, 0, 0)', (uid, gid))
    if res == 'win':
        c.execute('UPDATE user_points SET total_points = total_points + ?, wins = wins + 1 WHERE user_id = ?', (pts, uid))
    elif res == 'loss':
        c.execute('UPDATE user_points SET losses = losses + 1 WHERE user_id = ?', (uid,))
    else:
        c.execute('UPDATE user_points SET total_points = total_points + ?, draws = draws + 1 WHERE user_id = ?', (pts//2, uid))
    c.execute('SELECT total_points FROM user_points WHERE user_id = ?', (uid,))
    tot = c.fetchone()[0]
    lvl = (tot // 100) + 1
    c.execute('UPDATE user_points SET level = ? WHERE user_id = ?', (lvl, uid))
    cn.commit()
    cn.close()
    return lvl

def gtstats(uid):
    cn = sqlite3.connect('games.db')
    c = cn.cursor()
    c.execute('SELECT * FROM user_points WHERE user_id = ?', (uid,))
    r = c.fetchone()
    cn.close()
    return r

class TTTView(discord.ui.View):
    def __init__(self, p1, p2):
        super().__init__(timeout=300)
        self.p1 = p1
        self.p2 = p2
        self.cur = p1
        self.brd = [' '] * 9
        self.over = False
        
    def chkwin(self):
        ws = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for w in ws:
            if self.brd[w[0]] == self.brd[w[1]] == self.brd[w[2]] != ' ':
                return self.brd[w[0]]
        if ' ' not in self.brd: return 'tie'
        return None
    
    def brdstr(self):
        em = []
        for i, c in enumerate(self.brd):
            if c == 'X': em.append('X')
            elif c == 'O': em.append('O')
            else: em.append(str(i+1))
        return f"```\n{em[0]} | {em[1]} | {em[2]}\n--+---+--\n{em[3]} | {em[4]} | {em[5]}\n--+---+--\n{em[6]} | {em[7]} | {em[8]}\n```"
    
    async def mv(self, intr, pos):
        if self.over or intr.user != self.cur: return
        if self.brd[pos] != ' ':
            await intr.response.send_message("Taken!", ephemeral=True)
            return
        
        sym = 'X' if self.cur == self.p1 else 'O'
        self.brd[pos] = sym
        win = self.chkwin()
        emb = discord.Embed(title="Tic Tac Toe", color=0x00ff00)
        
        if win:
            self.over = True
            if win == 'tie':
                emb.description = f"Tie!\n\n{self.brdstr()}"
                addpts(self.p1.id, intr.guild.id, 5, 'draw')
                addpts(self.p2.id, intr.guild.id, 5, 'draw')
            else:
                wnr = self.p1 if sym == 'X' else self.p2
                lsr = self.p2 if sym == 'X' else self.p1
                emb.description = f"{wnr.mention} wins!\n\n{self.brdstr()}"
                addpts(wnr.id, intr.guild.id, 15, 'win')
                addpts(lsr.id, intr.guild.id, 0, 'loss')
            for x in self.children: x.disabled = True
        else:
            self.cur = self.p2 if self.cur == self.p1 else self.p1
            emb.description = f"{self.cur.mention}'s turn\n\n{self.brdstr()}"
        
        await intr.response.edit_message(embed=emb, view=self)
    
    @discord.ui.button(label='1', style=discord.ButtonStyle.secondary, row=0)
    async def b1(self, intr, btn): await self.mv(intr, 0)
    @discord.ui.button(label='2', style=discord.ButtonStyle.secondary, row=0)
    async def b2(self, intr, btn): await self.mv(intr, 1)
    @discord.ui.button(label='3', style=discord.ButtonStyle.secondary, row=0)
    async def b3(self, intr, btn): await self.mv(intr, 2)
    @discord.ui.button(label='4', style=discord.ButtonStyle.secondary, row=1)
    async def b4(self, intr, btn): await self.mv(intr, 3)
    @discord.ui.button(label='5', style=discord.ButtonStyle.secondary, row=1)
    async def b5(self, intr, btn): await self.mv(intr, 4)
    @discord.ui.button(label='6', style=discord.ButtonStyle.secondary, row=1)
    async def b6(self, intr, btn): await self.mv(intr, 5)
    @discord.ui.button(label='7', style=discord.ButtonStyle.secondary, row=2)
    async def b7(self, intr, btn): await self.mv(intr, 6)
    @discord.ui.button(label='8', style=discord.ButtonStyle.secondary, row=2)
    async def b8(self, intr, btn): await self.mv(intr, 7)
    @discord.ui.button(label='9', style=discord.ButtonStyle.secondary, row=2)
    async def b9(self, intr, btn): await self.mv(intr, 8)
    
    @discord.ui.button(label='Quit', style=discord.ButtonStyle.danger, row=3)
    async def qt(self, intr, btn):
        if intr.user not in [self.p1, self.p2]: return
        self.over = True
        emb = discord.Embed(title="TTT - Quit", description=f"{intr.user.mention} quit!", color=0xff0000)
        for x in self.children: x.disabled = True
        await intr.response.edit_message(embed=emb, view=self)
    
    @discord.ui.button(label='Rematch', style=discord.ButtonStyle.success, row=3)
    async def rm(self, intr, btn):
        if intr.user not in [self.p1, self.p2]: return
        nv = TTTView(self.p1, self.p2)
        emb = discord.Embed(title="TTT Rematch", description=f"{self.p1.mention} vs {self.p2.mention}\n\n{nv.brdstr()}", color=0x00ff00)
        await intr.response.edit_message(embed=emb, view=nv)

class TTTAI:
    def best(self, brd):
        for i in range(9):
            if brd[i] == ' ':
                brd[i] = 'O'
                if self.chk(brd) == 'O':
                    brd[i] = ' '
                    return i
                brd[i] = ' '
        for i in range(9):
            if brd[i] == ' ':
                brd[i] = 'X'
                if self.chk(brd) == 'X':
                    brd[i] = ' '
                    return i
                brd[i] = ' '
        if brd[4] == ' ': return 4
        cors = [i for i in [0, 2, 6, 8] if brd[i] == ' ']
        if cors: return random.choice(cors)
        avail = [i for i in range(9) if brd[i] == ' ']
        return random.choice(avail) if avail else None
    
    def chk(self, brd):
        ws = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for w in ws:
            if brd[w[0]] == brd[w[1]] == brd[w[2]] != ' ':
                return brd[w[0]]
        return None

class TTTAIView(discord.ui.View):
    def __init__(self, plr):
        super().__init__(timeout=300)
        self.plr = plr
        self.brd = [' '] * 9
        self.over = False
        self.ai = TTTAI()
        
    def chkwin(self):
        ws = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for w in ws:
            if self.brd[w[0]] == self.brd[w[1]] == self.brd[w[2]] != ' ':
                return self.brd[w[0]]
        if ' ' not in self.brd: return 'tie'
        return None
    
    def brdstr(self):
        em = []
        for i, c in enumerate(self.brd):
            if c == 'X': em.append('X')
            elif c == 'O': em.append('O')
            else: em.append(str(i+1))
        return f"```\n{em[0]} | {em[1]} | {em[2]}\n--+---+--\n{em[3]} | {em[4]} | {em[5]}\n--+---+--\n{em[6]} | {em[7]} | {em[8]}\n```"
    
    async def mv(self, intr, pos):
        if self.over or intr.user != self.plr: return
        if self.brd[pos] != ' ':
            await intr.response.send_message("Taken!", ephemeral=True)
            return
        
        self.brd[pos] = 'X'
        win = self.chkwin()
        if win:
            await self.end(intr, win)
            return
        
        am = self.ai.best(self.brd)
        if am is not None: self.brd[am] = 'O'
        win = self.chkwin()
        if win:
            await self.end(intr, win)
        else:
            emb = discord.Embed(title="TTT vs AI", description=f"Your turn\n\n{self.brdstr()}", color=0x00ff00)
            await intr.response.edit_message(embed=emb, view=self)
    
    async def end(self, intr, win):
        self.over = True
        emb = discord.Embed(title="TTT vs AI", color=0x00ff00)
        if win == 'tie':
            emb.description = f"Draw!\n\n{self.brdstr()}"
            addpts(self.plr.id, intr.guild.id, 8, 'draw')
        elif win == 'X':
            emb.description = f"{self.plr.mention} wins!\n\n{self.brdstr()}"
            addpts(self.plr.id, intr.guild.id, 20, 'win')
        else:
            emb.description = f"AI wins!\n\n{self.brdstr()}"
            addpts(self.plr.id, intr.guild.id, 0, 'loss')
        for x in self.children: x.disabled = True
        await intr.response.edit_message(embed=emb, view=self)
    
    @discord.ui.button(label='1', style=discord.ButtonStyle.secondary, row=0)
    async def ab1(self, intr, btn): await self.mv(intr, 0)
    @discord.ui.button(label='2', style=discord.ButtonStyle.secondary, row=0)
    async def ab2(self, intr, btn): await self.mv(intr, 1)
    @discord.ui.button(label='3', style=discord.ButtonStyle.secondary, row=0)
    async def ab3(self, intr, btn): await self.mv(intr, 2)
    @discord.ui.button(label='4', style=discord.ButtonStyle.secondary, row=1)
    async def ab4(self, intr, btn): await self.mv(intr, 3)
    @discord.ui.button(label='5', style=discord.ButtonStyle.secondary, row=1)
    async def ab5(self, intr, btn): await self.mv(intr, 4)
    @discord.ui.button(label='6', style=discord.ButtonStyle.secondary, row=1)
    async def ab6(self, intr, btn): await self.mv(intr, 5)
    @discord.ui.button(label='7', style=discord.ButtonStyle.secondary, row=2)
    async def ab7(self, intr, btn): await self.mv(intr, 6)
    @discord.ui.button(label='8', style=discord.ButtonStyle.secondary, row=2)
    async def ab8(self, intr, btn): await self.mv(intr, 7)
    @discord.ui.button(label='9', style=discord.ButtonStyle.secondary, row=2)
    async def ab9(self, intr, btn): await self.mv(intr, 8)
    
    @discord.ui.button(label='Quit', style=discord.ButtonStyle.danger, row=3)
    async def aqt(self, intr, btn):
        if intr.user != self.plr: return
        self.over = True
        emb = discord.Embed(title="TTT vs AI - Quit", color=0xff0000)
        for x in self.children: x.disabled = True
        await intr.response.edit_message(embed=emb, view=self)
    
    @discord.ui.button(label='Rematch', style=discord.ButtonStyle.success, row=3)
    async def arm(self, intr, btn):
        if intr.user != self.plr: return
        nv = TTTAIView(self.plr)
        emb = discord.Embed(title="TTT vs AI", description=f"Your turn\n\n{nv.brdstr()}", color=0x00ff00)
        await intr.response.edit_message(embed=emb, view=nv)

class RPSView(discord.ui.View):
    def __init__(self, ch, op):
        super().__init__(timeout=60)
        self.ch = ch
        self.op = op
        self.picks = {}
        
    @discord.ui.button(label='Rock', style=discord.ButtonStyle.primary)
    async def rck(self, intr, btn): await self.pick(intr, 'rock')
    @discord.ui.button(label='Paper', style=discord.ButtonStyle.primary)  
    async def ppr(self, intr, btn): await self.pick(intr, 'paper')
    @discord.ui.button(label='Scissors', style=discord.ButtonStyle.primary)
    async def scs(self, intr, btn): await self.pick(intr, 'scissors')
    
    @discord.ui.button(label='Quit', style=discord.ButtonStyle.danger, row=1)
    async def qt(self, intr, btn):
        if intr.user not in [self.ch, self.op]: return
        emb = discord.Embed(title="RPS - Quit", color=0xff0000)
        for x in self.children: x.disabled = True
        await intr.response.edit_message(embed=emb, view=self)
    
    async def pick(self, intr, c):
        if intr.user not in [self.ch, self.op]:
            await intr.response.send_message("Not your game!", ephemeral=True)
            return
        self.picks[intr.user.id] = c
        if len(self.picks) == 1:
            await intr.response.send_message("Locked! Waiting...", ephemeral=True)
        else:
            p1c = self.picks[self.ch.id]
            p2c = self.picks[self.op.id]
            res = self.gtwn(p1c, p2c)
            
            emb = discord.Embed(title="RPS Results!", color=0x00ff00)
            emojis = {'rock': 'R', 'paper': 'P', 'scissors': 'S'}
            emb.add_field(name=self.ch.display_name, value=f"{emojis[p1c]} {p1c.title()}", inline=True)
            emb.add_field(name="VS", value="vs", inline=True)
            emb.add_field(name=self.op.display_name, value=f"{emojis[p2c]} {p2c.title()}", inline=True)
            
            if res == 'tie':
                emb.description = "Tie!"
                addpts(self.ch.id, intr.guild.id, 3, 'draw')
                addpts(self.op.id, intr.guild.id, 3, 'draw')
            elif res == 'p1':
                emb.description = f"{self.ch.mention} wins!"
                addpts(self.ch.id, intr.guild.id, 10, 'win')
                addpts(self.op.id, intr.guild.id, 0, 'loss')
            else:
                emb.description = f"{self.op.mention} wins!"
                addpts(self.op.id, intr.guild.id, 10, 'win')
                addpts(self.ch.id, intr.guild.id, 0, 'loss')
            
            for x in self.children: x.disabled = True
            await intr.response.edit_message(embed=emb, view=self)
    
    def gtwn(self, p1, p2):
        if p1 == p2: return 'tie'
        wins = {'rock': 'scissors', 'paper': 'rock', 'scissors': 'paper'}
        return 'p1' if wins[p1] == p2 else 'p2'

@bot.tree.command(name="tictactoe", description="Play TTT")
async def ttt(intr, opponent: discord.Member = None):
    if opponent and opponent.bot and opponent != bot.user:
        await intr.response.send_message("No bots!", ephemeral=True)
        return
    if opponent == intr.user:
        await intr.response.send_message("No self!", ephemeral=True)
        return
    
    if opponent is None or opponent == bot.user:
        v = TTTAIView(intr.user)
        emb = discord.Embed(title="TTT vs AI", description=f"Your turn (X)\n\n{v.brdstr()}", color=0x00ff00)
    else:
        v = TTTView(intr.user, opponent)
        emb = discord.Embed(title="Tic Tac Toe", description=f"{intr.user.mention} vs {opponent.mention}\n\n{v.brdstr()}", color=0x00ff00)
    await intr.response.send_message(embed=emb, view=v)

@bot.tree.command(name="rps", description="Rock Paper Scissors")
async def rps(intr, opponent: discord.Member = None):
    if opponent and opponent.bot and opponent != bot.user:
        await intr.response.send_message("No bots!", ephemeral=True)
        return
    if opponent == intr.user:
        await intr.response.send_message("No self!", ephemeral=True)
        return
    
    if opponent is None or opponent == bot.user:
        bc = random.choice(['rock', 'paper', 'scissors'])
        emb = discord.Embed(title="RPS vs AI", description="Pick!", color=0x00ff00)
        v = discord.ui.View()
        
        async def aicb(i, uc):
            if i.user != intr.user:
                await i.response.send_message("Not yours!", ephemeral=True)
                return
            emojis = {'rock': 'R', 'paper': 'P', 'scissors': 'S'}
            remb = discord.Embed(title="RPS Results!", color=0x00ff00)
            remb.add_field(name="You", value=f"{emojis[uc]} {uc.title()}", inline=True)
            remb.add_field(name="VS", value="vs", inline=True)
            remb.add_field(name="AI", value=f"{emojis[bc]} {bc.title()}", inline=True)
            
            if uc == bc:
                remb.description = "Tie!"
                addpts(i.user.id, i.guild.id, 3, 'draw')
            elif (uc == 'rock' and bc == 'scissors') or (uc == 'paper' and bc == 'rock') or (uc == 'scissors' and bc == 'paper'):
                remb.description = "You win!"
                addpts(i.user.id, i.guild.id, 8, 'win')
            else:
                remb.description = "AI wins!"
                addpts(i.user.id, i.guild.id, 0, 'loss')
            await i.response.edit_message(embed=remb, view=None)
        
        rb = discord.ui.Button(label='Rock', style=discord.ButtonStyle.primary)
        pb = discord.ui.Button(label='Paper', style=discord.ButtonStyle.primary)
        sb = discord.ui.Button(label='Scissors', style=discord.ButtonStyle.primary)
        rb.callback = lambda i: aicb(i, 'rock')
        pb.callback = lambda i: aicb(i, 'paper')
        sb.callback = lambda i: aicb(i, 'scissors')
        v.add_item(rb)
        v.add_item(pb)
        v.add_item(sb)
        await intr.response.send_message(embed=emb, view=v)
    else:
        emb = discord.Embed(title="RPS", description=f"{intr.user.mention} vs {opponent.mention}\n\nPick!", color=0x00ff00)
        v = RPSView(intr.user, opponent)
        await intr.response.send_message(embed=emb, view=v)

triv = {
    "general": [
        {"q": "Capital of France?", "a": ["paris"], "w": ["london", "berlin", "madrid"]},
        {"q": "How many continents?", "a": ["7", "seven"], "w": ["6", "8", "5"]},
        {"q": "Largest planet?", "a": ["jupiter"], "w": ["saturn", "earth", "mars"]},
    ],
    "gaming": [
        {"q": "Who made Minecraft?", "a": ["mojang"], "w": ["microsoft", "sony", "nintendo"]},
        {"q": "Main character in Zelda?", "a": ["link"], "w": ["zelda", "ganon", "mario"]},
    ],
    "science": [
        {"q": "Chemical symbol for water?", "a": ["h2o"], "w": ["co2", "o2", "h2"]},
        {"q": "Bones in adult body?", "a": ["206"], "w": ["207", "205", "210"]},
    ]
}

@bot.tree.command(name="trivia", description="Trivia game")
@app_commands.choices(category=[
    app_commands.Choice(name="General", value="general"),
    app_commands.Choice(name="Gaming", value="gaming"),
    app_commands.Choice(name="Science", value="science"),
])
async def trv(intr, category: str = "general"):
    q = random.choice(triv[category])
    opts = q["w"][:3] + [random.choice(q["a"])]
    random.shuffle(opts)
    
    emb = discord.Embed(title=f"Trivia - {category.title()}", description=f"**{q['q']}**", color=0x3498db)
    ems = ["A", "B", "C", "D"]
    for i, o in enumerate(opts):
        emb.add_field(name=f"{ems[i]}. {o.title()}", value="", inline=False)
    
    v = discord.ui.View(timeout=20)
    
    async def anscb(i, ans):
        if i.user != intr.user:
            await i.response.send_message("Not yours!", ephemeral=True)
            return
        cor = ans.lower() in [a.lower() for a in q["a"]]
        remb = discord.Embed(title="Trivia", color=0x00ff00 if cor else 0xff0000)
        if cor:
            remb.description = f"Correct! {q['q']}"
            addpts(i.user.id, i.guild.id, 10, 'win')
        else:
            remb.description = f"Wrong! Answer: {q['a'][0]}"
            addpts(i.user.id, i.guild.id, 0, 'loss')
        await i.response.edit_message(embed=remb, view=None)
    
    for i, o in enumerate(opts):
        btn = discord.ui.Button(label=f"{ems[i]}. {o.title()}", style=discord.ButtonStyle.secondary)
        btn.callback = lambda inter, ans=o: anscb(inter, ans)
        v.add_item(btn)
    
    await intr.response.send_message(embed=emb, view=v)

@bot.tree.command(name="guess", description="Guess number game")
@app_commands.choices(difficulty=[
    app_commands.Choice(name="Easy (1-50)", value="easy"),
    app_commands.Choice(name="Medium (1-100)", value="medium"),
    app_commands.Choice(name="Hard (1-200)", value="hard")
])
async def gss(intr, difficulty: str = "medium"):
    rngs = {"easy": 50, "medium": 100, "hard": 200}
    mx = rngs[difficulty]
    num = random.randint(1, mx)
    gid = f"{intr.user.id}_{intr.id}"
    mxg = 7 if difficulty == "easy" else 6 if difficulty == "medium" else 8
    bot.games[gid] = {'num': num, 'gs': 0, 'mxg': mxg, 'rng': mx, 'dif': difficulty}
    
    emb = discord.Embed(title=f"Guess - {difficulty.title()}", description=f"1-{mx}, {mxg} guesses", color=0xf39c12)
    await intr.response.send_message(embed=emb)
    
    def chk(m): return m.author == intr.user and m.channel == intr.channel and m.content.isdigit()
    
    while gid in bot.games:
        try:
            msg = await bot.wait_for('message', check=chk, timeout=60.0)
            g = int(msg.content)
            gd = bot.games[gid]
            gd['gs'] += 1
            
            if g == gd['num']:
                pts = 10 + max(0, (gd['mxg'] - gd['gs']) * 2)
                emb = discord.Embed(title="Win!", description=f"It was {gd['num']}! ({gd['gs']} tries)", color=0x00ff00)
                addpts(intr.user.id, intr.guild.id, pts, 'win')
                await msg.reply(embed=emb)
                del bot.games[gid]
                break
            elif gd['gs'] >= gd['mxg']:
                emb = discord.Embed(title="Over", description=f"It was {gd['num']}", color=0xff0000)
                addpts(intr.user.id, intr.guild.id, 0, 'loss')
                await msg.reply(embed=emb)
                del bot.games[gid]
                break
            else:
                rem = gd['mxg'] - gd['gs']
                hint = "higher" if g < gd['num'] else "lower"
                emb = discord.Embed(title="Wrong", description=f"Go {hint}! ({rem} left)", color=0xf39c12)
                await msg.reply(embed=emb)
        except asyncio.TimeoutError:
            if gid in bot.games:
                emb = discord.Embed(title="Timeout", description=f"It was {bot.games[gid]['num']}", color=0xff0000)
                await intr.followup.send(embed=emb)
                del bot.games[gid]
            break

@bot.tree.command(name="stats", description="Your stats")
async def sts(intr, user: discord.Member = None):
    tgt = user or intr.user
    if tgt.bot:
        await intr.response.send_message("Bots have no stats!", ephemeral=True)
        return
    
    ud = gtstats(tgt.id)
    if not ud:
        emb = discord.Embed(title="Stats", description=f"{tgt.display_name} hasn't played yet!", color=0x95a5a6)
    else:
        _, _, pts, lvl, wins, losses, draws = ud
        tot = wins + losses + draws
        wr = round((wins / tot * 100), 1) if tot > 0 else 0
        emb = discord.Embed(title=f"{tgt.display_name}", color=0x3498db)
        emb.add_field(name="Level", value=str(lvl), inline=True)
        emb.add_field(name="Points", value=str(pts), inline=True)
        emb.add_field(name="Win Rate", value=f"{wr}%", inline=True)
        emb.add_field(name="W/L/D", value=f"{wins}/{losses}/{draws}", inline=True)
    await intr.response.send_message(embed=emb)

@bot.tree.command(name="leaderboard", description="Server leaderboard")
async def lb(intr):
    cn = sqlite3.connect('games.db')
    c = cn.cursor()
    c.execute('SELECT user_id, total_points, level, wins FROM user_points WHERE guild_id = ? ORDER BY total_points DESC LIMIT 10', (intr.guild.id,))
    res = c.fetchall()
    cn.close()
    
    if not res:
        await intr.response.send_message("No games played yet!")
        return
    
    emb = discord.Embed(title="Leaderboard", color=0xf1c40f)
    mds = ["1.", "2.", "3."]
    txt = []
    for i, (uid, pts, lvl, wins) in enumerate(res):
        u = intr.guild.get_member(uid)
        if not u: continue
        md = mds[i] if i < 3 else f"`#{i+1}`"
        txt.append(f"{md} **{u.display_name}** - {pts} pts")
    emb.description = "\n".join(txt[:10])
    await intr.response.send_message(embed=emb)

@bot.tree.command(name="8ball", description="Magic 8 ball")
async def eball(intr, question: str):
    ans = random.choice([
        "Yes", "No", "Maybe", "Definitely", "Doubtful", "Ask again",
        "Without a doubt", "Very doubtful", "Most likely", "Outlook good"
    ])
    emb = discord.Embed(title="8 Ball", color=0x9b59b6)
    emb.add_field(name="Q", value=question, inline=False)
    emb.add_field(name="A", value=f"*{ans}*", inline=False)
    addpts(intr.user.id, intr.guild.id, 1, 'draw')
    await intr.response.send_message(embed=emb)

@bot.tree.command(name="coinflip", description="Flip a coin")
@app_commands.choices(call=[
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails")
])
async def cf(intr, call: str = None):
    res = random.choice(["heads", "tails"])
    emb = discord.Embed(title="Coin Flip", color=0xe67e22)
    if call:
        cor = call.lower() == res
        emb.description = f"{'Correct!' if cor else 'Wrong!'}\nResult: {res.title()}"
        if cor: addpts(intr.user.id, intr.guild.id, 5, 'win')
        else: addpts(intr.user.id, intr.guild.id, 0, 'loss')
    else:
        emb.description = f"**{res.title()}**"
        addpts(intr.user.id, intr.guild.id, 1, 'draw')
    await intr.response.send_message(embed=emb)

@bot.tree.command(name="dice", description="Roll dice")
async def dc(intr, sides: int = 6, count: int = 1):
    if sides < 2 or sides > 100:
        await intr.response.send_message("2-100 sides only!", ephemeral=True)
        return
    if count < 1 or count > 10:
        await intr.response.send_message("1-10 dice only!", ephemeral=True)
        return
    
    rolls = [random.randint(1, sides) for _ in range(count)]
    tot = sum(rolls)
    emb = discord.Embed(title=f"{count}d{sides}", color=0xe74c3c)
    if count == 1:
        emb.description = f"**{rolls[0]}**"
    else:
        emb.description = f"{', '.join(map(str, rolls))}\nTotal: **{tot}**"
    
    lck = tot / (count * sides)
    pts = 8 if lck >= 0.8 else 4 if lck >= 0.6 else 1
    addpts(intr.user.id, intr.guild.id, pts, 'draw')
    await intr.response.send_message(embed=emb)

if __name__ == "__main__":
    try:
        bot.run(tkn)
    except:
        pass
