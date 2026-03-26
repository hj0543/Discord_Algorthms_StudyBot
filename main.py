import asyncio

import discord
from discord.ext import commands

from config import COMMAND_PREFIX, TOKEN

# 필요한 권한만 명시적으로 켜 두면 디버깅 포인트가 줄고 권한 오남용도 막을 수 있다.
intents = discord.Intents.default()
intents.message_content = True

# 봇 생성은 한 곳에서 고정해 두고, 이후 확장 로딩만 분리해서 관리한다.
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="알고리즘 스터디 봇"))

    # 배포 직후 슬래시 명령이 오래된 상태로 남는 문제를 막기 위해 시작 시 즉시 동기화한다.
    try:
        synced = await bot.tree.sync()
        print(f"총 {len(synced)}개의 슬래시 명령이 동기화되었습니다.")
    except Exception as e:
        print(f"슬래시 명령 동기화 실패: {e}")


# 자동 동기화가 누락되는 상황을 대비해 수동 복구용 sync 명령도 남겨 둔다.
@bot.command()
async def sync(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"총 {len(synced)}개의 슬래시 명령이 동기화되었습니다.")
    except Exception as e:
        await ctx.send(f"슬래시 명령 동기화 실패: {e}")


async def load_extensions():
    # Cog 단위로 기능을 분리해 두면 파일이 커져도 책임 경계가 유지된다.
    await bot.load_extension("cogs.study")


async def main():
    # bot 컨텍스트 안에서 실행하면 시작과 종료 자원이 더 안정적으로 정리된다.
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
