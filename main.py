from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks


ALARM_CHANNEL = "CHANNEL_ID"  # 面倒なのでチャンネルは一元化。大丈夫だ、問題ない。


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


@tasks.loop(1)
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
                embed.add_field("時刻", f"{t_format}")
                embed.add_field("アラーム名", target[1])
                await bot.get_channel(ALARM_CHANNEL).send(target[0].mention, embed)
            del queue.queue[0]
            return
check_queue.start()


@bot.command()
async def alarm(ctx, time):
    time_h, time_m = time.split(":")
    if int(time_h) >= 24 or int(time_m) >= 60:
        await ctx.send(ctx.author.mention + "Time must be lile `12:34`")
        return
    target_time = alarm_format(time_h, time_m)
    target_stamp = int(datetime.timestamp(target_time))
    queueItem = (target_stamp, ctx.author.id)
    queue.queue.append(queueItem)
    queue.queue.sort()


@bot.command()
async def alarms(ctx):
    user = ctx.author.id
    registered_item = queue.set_by(user)
    embed = discord.Embed(
        title=f"{ctx.author.name}#{ctx.author.discriminator} さんのアラーム", color=0x00bfff)
    for item in registered_item:
        embed.add_field(item[0], item[1])
    # Todo embedのもうちょい
    await ctx.send(embed)


def alarm_format(time_h, time_m):
    now = datetime.now()
    if int(time_h) < now.hour or (int(time_h) == now.hour and int(time_m) <= now.minute):
        now += timedelta(days=1)
    result = datetime.strptime(
        f"{now.year}/{now.month}/{now.day} {time_h}:{time_m}", "%Y/%m/%d %H:%M")
    return result


bot.run("とー君")
