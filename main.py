from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks

import os
PATH = os.path.dirname(os.path.abspath(__file__))

TOKEN_PATH = PATH + "/token.txt"
def token(): return [(f.read(), f.close()) for f in [open(TOKEN_PATH)]][0][0]


CH_PATH = PATH + "/channel.txt"
def alarm_ch(): return [(f.read(), f.close()) for f in [open(CH_PATH)]][0][0]


ALARM_CHANNEL = alarm_ch()  # 面倒なのでチャンネルは一元化。大丈夫だ、問題ない。


class Alarm_Queue:
    """アラームのキュー操作クラス

    """

    def __init__(self):
        self.queue = []

    def set(self, item: dict):
        """
        Example
        ---------
        self.set({"time": TIMESTAMP, "target": [(ctx.author.id, "NAME")]})
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
            return

    def set_by(self, user) -> list:
        result = []
        for i in self.queue:
            for t in i["target"]:
                if t[0] == user:
                    time = datetime.fromtimestamp(float(i["time"]))
                    t_format = f"{time.hour}:{time.minute}"
                    result.append((t_format, t[1]))
        return result


queue = Alarm_Queue()


bot = commands.Bot("&")


@tasks.loop(seconds=1)
async def check_queue():
    now = int(datetime.timestamp(datetime.now()))
    if queue.queue:
        item = queue.queue[0]
        if item["time"] <= now:
            time = datetime.fromtimestamp(float(item["time"]))
            t_format = f"{time.hour}:{time.minute}"
            for target in item["target"]:
                # Todo for-awaitの検証
                embed = discord.Embed(title="時間です", color=0x00bfff)
                embed.add_field(name="時刻", value=f"{t_format}", inline=True)
                embed.add_field(name="アラーム名", value=target[1], inline=True)
                send_to = bot.get_channel(int(ALARM_CHANNEL))
                target_user = bot.get_user(target[0])
                await send_to.send(target_user.mention, embed=embed)
            del queue.queue[0]
            return


@bot.event
async def on_ready():
    print(ALARM_CHANNEL)
    check_queue.start()
    pass


@bot.command()
async def alarm(ctx, time, name="NONE"):
    time_h, time_m = time.split(":")
    if int(time_h) >= 24 or int(time_m) >= 60:
        await ctx.send(ctx.author.mention + f"タイマー設定コマンドの形式は ```&alarm [時(24時間表記):分] [通知するアラーム名(任意)]``` ")
        return
    target_stamp = int(datetime.timestamp(alarm_format(time_h, time_m)))
    t_format = f"{time_h}:{time_m}"
    queueItem = {"time": target_stamp, "target": [(ctx.author.id, name)]}
    queue.set(queueItem)
    embed = discord.Embed(title="アラームをセットしました", color=0x00bfff)
    embed.add_field(name="時刻", value=t_format, inline=True)
    embed.add_field(name="名前", value=name, inline=True)
    await ctx.send(embed=embed)


@bot.command()
async def alarms(ctx):
    user = ctx.author.id
    registered_item = queue.set_by(user)
    embed = discord.Embed(
        title=f"{ctx.author.name}#{ctx.author.discriminator} さんのアラーム", color=0x00bfff)
    for item in registered_item:
        embed.add_field(name=item[0], value=item[1], inline=True)
    # Todo embedのもうちょい
    await ctx.send(embed=embed)


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


bot.run(token(), reconnect=True)
