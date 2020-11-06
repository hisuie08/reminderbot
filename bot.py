import aiohttp
import os
import sys
from datetime import datetime, timedelta
try:
    import pysqlite3
except ImportError:
    import sqlite3
import discord
from discord.ext import commands, tasks

PATH = os.path.dirname(os.path.abspath(__file__))

QUEUE_DB_PATH = PATH + "/alarmqueue.db"
TOKEN_PATH = PATH + "/token.txt"
def token(): return [(f.read(), f.close()) for f in [open(TOKEN_PATH)]][0][0]


MAX_ALARM_PER_USER = 10


class Alarm_Queue:
    """アラームのキュー操作クラス

    """

    def __init__(self):

        self.connection = sqlite3.connect(QUEUE_DB_PATH, isolation_level=None)
        try:
            self.connection.execute(
                '''create table alarms(timestamp Integer, userid Integer, channel Integer, name Text)''')
        except sqlite3.OperationalError:
            pass
        self.cursor = self.connection.cursor()

    def cancel(self, user, name):
        """
        """
        query = f"delete from alarms where userid = {user}"
        if not name == "ALL":
            query += f" and name = '{name}'"
        try:
            self.cursor.execute(query)
            self.connection.commit()
            return True
        except Exception:
            return False

    def solve(self, timestamp):
        self.cursor.execute(
            f"delete from alarms where timestamp <= {timestamp}")

    def set(self, timestamp, userid, channel, name):
        """
        """
        self.cursor.execute("insert into alarms (timestamp, userid,channel,name) values (?,?,?,?)",
                            (timestamp, userid, channel, name))
        self.connection.commit()

    def set_by(self, user) -> list:
        """
        """
        self.cursor.execute(
            f"select * from alarms where userid = {user} order by timestamp")
        result = self.cursor.fetchall()
        self.connection.commit()
        return result

    def time_up(self, timestamp) -> list:
        """
        """
        self.cursor.execute(
            f"select * from alarms where timestamp <= {timestamp}")
        result = self.cursor.fetchall()
        self.connection.commit()
        return result


bot = commands.Bot(("&"))


@tasks.loop(seconds=1)
async def check_queue():
    now = int(datetime.timestamp(datetime.now()))
    for item in queue.time_up(now):
        time = datetime.fromtimestamp(float(now))
        target_author = bot.get_user(item[1])
        target_ch = bot.get_channel(item[2])
        name = item[3]
        t_format = f"{time.hour}:{time.minute}"
        embed = discord.Embed(title="時間です", color=0x00bfff)
        embed.add_field(name=f"**{name}**", value=t_format, inline=True)
        await target_ch.send(target_author.mention, embed=embed)
    queue.solve(now)
    return


@bot.event
async def on_ready():
    check_queue.start()
    pass


@bot.command()
async def alarm(ctx, time, name=None):
    """
    アラーム登録コマンド
    """
    print(
        f"[Command] #{ctx.channel.id} @{ctx.author.id} : {ctx.message.content}")
    if len(queue.set_by(ctx.author.id)) > MAX_ALARM_PER_USER:
        await ctx.send(ctx.author.mention
                       + f"1ユーザーが登録できるアラームは最大{MAX_ALARM_PER_USER}です。\
                           ```&cancel [アラーム名]```で不要なアラームを削除してください")
    time_h, time_m = time.split(":")
    if int(time_h) >= 24 or int(time_m) >= 60:
        await ctx.send(ctx.author.mention
                       + f"タイマー設定コマンドの形式は ```&alarm [時(24時間表記):分] [通知するアラーム名(任意)]``` ")
        return
    target_stamp = int(datetime.timestamp(alarm_format(time_h, time_m)))
    t_format = f"{time_h}:{time_m}"
    if name is not None:
        name = name
    else:
        name = t_format
    queue.set(target_stamp, ctx.author.id, ctx.channel.id, name)
    embed = discord.Embed(title="アラームをセットしました", color=0x00bfff)
    embed.add_field(name="アラーム名", value=name, inline=True)
    embed.add_field(name="時刻", value=t_format, inline=True)
    await ctx.send(embed=embed)
    return


@bot.command()
async def alarms(ctx):
    """
    アラームリスト表示
    """
    print(f"[Command] @{ctx.author.id} : {ctx.message.content}")
    user = ctx.author.id
    registered_item = queue.set_by(user)
    embed = discord.Embed(
        title=f"{ctx.author.name}#{ctx.author.discriminator} さんのアラーム", color=0x00bfff)
    for item in registered_item:
        time = datetime.fromtimestamp(float(item[0])).strftime("%H:%M")
        embed.add_field(
            name=f"{item[3]}", value=f"{time}", inline=True)
    await ctx.send(embed=embed)
    return


@bot.command()
async def cancel(ctx, name):
    """
    アラームキャンセルコマンド
    """
    print(f"[Command] @{ctx.author.id} : {ctx.message.content}")
    user = ctx.author.id
    if queue.cancel(user, name=name):
        embed = discord.Embed(title="削除成功", color=0x00bfff)
        embed.description = f"アラーム {name} を削除しました"
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="削除失敗", color=0xff0000)
        embed.description = f"アラーム {name} は存在しません"
        await ctx.send(embed=embed)
    return


def alarm_format(time_h, time_m):
    """
    時,分を引数にdatetime型を錬成する関数。
    """
    now = datetime.now()
    if int(time_h) < now.hour or (int(time_h) == now.hour and int(time_m) <= now.minute):
        now += timedelta(days=1)
    result = datetime.strptime(
        f"{now.year}/{now.month}/{now.day} {time_h}:{time_m}", "%Y/%m/%d %H:%M")
    return result


if __name__ == "__main__":
    now = int(datetime.timestamp(datetime.now()))
    queue = Alarm_Queue()
    queue.solve(now)
    bot.run(token(), reconnect=True)
