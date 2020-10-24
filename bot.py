import os
import sys
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

PATH = os.path.dirname(os.path.abspath(__file__))

TOKEN_PATH = PATH + "/token.txt"
def token(): return [(f.read(), f.close()) for f in [open(TOKEN_PATH)]][0][0]


MAX_ALARM_PER_USER = 10


class Alarm_Queue:
    """アラームのキュー操作クラス

    """

    def __init__(self):
        self.queue = []

    def cancel(self, user, name):
        for item in self.queue:
            for target in item["target"]:
                if target[0] == user and target[2] == name:
                    item["target"].remove(target)
                    return True
        return False

    def set(self, item: dict):
        """
        Example
        ---------
        self.set({"time": TIMESTAMP, "target": [(ctx.author.id , ctx.channel.id , "NAME")]})
        """
        if self.queue:
            for i in self.queue:
                if i["time"] == item["time"]:
                    i["target"] += item["target"]
                    return
                else:
                    self.queue.append(item)
                    self.queue.sort(key=lambda x: x["time"])
                    return
        else:
            self.queue.append(item)
            self.queue.sort(key=lambda x: x["time"])
            print(self.queue)
            return

    def set_by(self, user) -> list:
        result = []
        for i in self.queue:
            for t in i["target"]:
                if t[0] == user:
                    time = datetime.fromtimestamp(float(i["time"]))
                    t_format = f"{time.hour}:{time.minute}"
                    result.append((t_format, t[2]))
        return result


bot = commands.Bot("&")
queue = Alarm_Queue()


@tasks.loop(seconds=1)
async def check_queue():
    now = int(datetime.timestamp(datetime.now()))
    if queue.queue:
        item = queue.queue[0]
        if item["time"] <= now:
            time = datetime.fromtimestamp(float(item["time"]))
            t_format = f"{time.hour}:{time.minute}"
            for target in item["target"]:
                target_user = bot.get_user(target[0])
                target_ch = bot.get_channel(target[1])
                target_name = target[2]
                embed = discord.Embed(title="時間です", color=0x00bfff)
                embed.add_field(name="時刻", value=f"{t_format}", inline=True)
                embed.add_field(name="アラーム名", value=target_name, inline=True)
                await target_ch.send(target_user.mention, embed=embed)
            queue.queue.pop(0)
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
    if name is not None:
        name = name
    else:
        name = f"{time_h}:{time_m}"
    target_stamp = int(datetime.timestamp(alarm_format(time_h, time_m)))
    t_format = f"{time_h}:{time_m}"
    queueItem = {"time": target_stamp, "target": [
        (ctx.author.id, ctx.channel.id, name)]}
    queue.set(queueItem)
    embed = discord.Embed(title="アラームをセットしました", color=0x00bfff)
    embed.add_field(name="時刻", value=t_format, inline=True)
    embed.add_field(name="名前", value=name, inline=True)
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
        embed.add_field(name=item[0], value=item[1], inline=True)
    await ctx.send(embed=embed)
    return


@bot.command()
async def cancel(ctx, name):
    """
    アラームキャンセルコマンド
    """
    print(f"[Command] @{ctx.author.id} : {ctx.message.content}")
    user = ctx.author.id
    if queue.cancel(user, name):
        await ctx.send(ctx.author.mention + f"アラーム {name} を削除しました")
    else:
        await ctx.send(ctx.author.mention + f"アラーム {name} は存在しません")
    return


@bot.command()
async def reload(ctx):
    os.execl(sys.executable, sys.executable, queue * sys.argv)


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
    print(sys.executable, sys.executable, *sys.argv)
    bot.run(token(), reconnect=True)
