import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils.solvedac import (
    get_problem_by_id, 
    get_user_info, 
    search_problems
)
from datetime import datetime, timedelta, timezone, time 
import random
import json
import os
import requests
import re

# 난이도별 데이터
TIER_DATA = {
    0: "Unrated",
    1: "Bronze V", 2: "Bronze IV", 3: "Bronze III", 4: "Bronze IV", 5: "Bronze I",
    6: "Silver V", 7: "Silver IV", 8: "Silver III", 9: "Silver II", 10: "Silver I",
    11: "Gold V", 12: "Gold IV", 13: "Gold III", 14: "Gold II", 15: "Gold I",
    16: "Platinum V", 17: "Platinum IV", 18: "Platinum III", 19: "Platinum II", 20: "Platinum I",
}

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "study_data.json" # 📂 데이터를 저장할 파일 이름
        self.members = {}
        self.alert_channel_id = None
        self.solve_alert_channel_id = None # 풀이 알림을 보낼 별도 채널
        self.announced_problems = [] # 공지된 문제 리스트
        self.solved_log = {}         # {유저ID: [해결한 문제들]}
        self.user_stats = {}         # {유저ID: {'tier': 0, 'class': 0}}
        self.load_data() # 🤖 클래스가 생성될 때 저장된 데이터를 불러옵니다.

    # 데이터를 파일(study_data.json)에 저장하는 함수
    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'members': {str(k): v for k, v in self.members.items()}, # ID는 문자열로 저장
                    'alert_channel_id': self.alert_channel_id,
                    'solve_alert_channel_id': self.solve_alert_channel_id,
                    'announced_problems': self.announced_problems, # 이제 [{'pid': '1000', 'deadline': '...'}, ...] 형식
                    'solved_log': {str(k): v for k, v in self.solved_log.items()}
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"데이터 저장 중 오류 발생: {e}")

    # 저장된 파일을 읽어와서 봇의 기억을 되살리는 함수
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 유저 ID는 다시 숫자로 변환 (JSON은 숫자를 키로 쓰지 못함)
                    self.members = {int(k): v for k, v in data.get('members', {}).items()}
                    self.alert_channel_id = data.get('alert_channel_id')
                    self.solve_alert_channel_id = data.get('solve_alert_channel_id')
                    
                    # 이전 버전 호환 (문자열 리스트였던 걸 딕셔너리로 변환)
                    self.announced_problems = []
                    for p in data.get('announced_problems', []):
                        if isinstance(p, dict):
                            self.announced_problems.append(p)
                        else:
                            self.announced_problems.append({'pid': p, 'deadline': (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")})
                    
                    self.solved_log = {}
                    for k, v in data.get('solved_log', {}).items():
                        if isinstance(v, list):
                            self.solved_log[int(k)] = {str(pid): "1970-01-01 00:00:00" for pid in v}
                        else:
                            self.solved_log[int(k)] = v
            except Exception as e:
                print(f"데이터 불러오기 중 오류 발생: {e}")

    # 봇이 준비를 다 마친 뒤 타이머를 안전하게 시작하는 곳
    async def cog_load(self):
        if not self.daily_alert.is_running():
            self.daily_alert.start()
        if not self.check_solutions.is_running():
            self.check_solutions.start()

    # 봇이 종료될 때 타이머도 안전하게 끄는 곳
    def cog_unload(self):
        self.daily_alert.cancel()
        self.check_solutions.cancel()

    # 1. /등록
    @app_commands.command(name="등록", description="백준 아이디를 봇에 등록합니다.")
    @app_commands.describe(handle="등록할 백준 아이디")
    async def register(self, interaction: discord.Interaction, handle: str):
        await interaction.response.defer()
        user_info = get_user_info(handle)
        if user_info:
            self.members[interaction.user.id] = handle
            self.save_data() # 저장!
            tier_int = user_info.get('tier', 0)
            tier_name = TIER_DATA.get(tier_int, "Unknown")
            await interaction.followup.send(f"✅ 등록 완료: **{handle}** ({tier_name})")
        else:
            await interaction.followup.send(f"❌ '{handle}' 계정을 찾을 수 없습니다.")

    # 2. /프로필
    @app_commands.command(name="프로필", description="내 정보 또는 다른 사용자의 정보를 확인합니다.")
    @app_commands.describe(handle="검색할 백준 아이디 (입력하지 않으면 내 프로필 검색)")
    async def profile(self, interaction: discord.Interaction, handle: str = None):
        await interaction.response.defer()
        
        # 1. 대상 아이디 결정 로직
        if handle is None:
            # 아이디를 입력하지 않은 경우: 내 프로필 검색
            target_handle = self.members.get(interaction.user.id)
            if not target_handle:
                await interaction.followup.send("먼저 `/등록` 해주세요! 또는 검색할 아이디를 같이 입력해주세요.")
                return
        else:
            # 아이디를 입력한 경우: 입력한 아이디로 검색
            target_handle = handle

        # 2. 유저 정보 조회
        user_info = get_user_info(target_handle)
        
        if user_info:
            tier_int = user_info.get('tier', 0)
            tier_name = TIER_DATA.get(tier_int, "Unknown")
            
            # 추가 정보 추출
            rating = user_info.get('rating', 0)
            solved = user_info.get('solvedCount', 0)
            streak = user_info.get('maxStreak', 0)
            rank = user_info.get('rank', 0)
            user_class = user_info.get('class', 0)
            bio = user_info.get('bio', '')
            
            # 프로필 이미지 처리
            profile_img = user_info.get('profileImageUrl')
            if profile_img:
                profile_img = f"https://wsrv.nl/?url={profile_img}&w=256&h=256&fit=cover"
            else:
                profile_img = "https://static.solved.ac/misc/360x360/default_profile.png"
                
            # 임베드 디자인 구성 (이모지 제거됨)
            embed = discord.Embed(
                title=f"[{tier_name}] {target_handle}님의 프로필",
                url=f"https://solved.ac/profile/{target_handle}",
                description=f"{bio}" if bio else "",
                color=discord.Color.blue()
            )
            
            embed.set_thumbnail(url=profile_img)
            embed.add_field(name="🏅 티어", value=f"**{tier_name}**", inline=True)
            embed.add_field(name="📈 레이팅", value=f"**{rating:,}**", inline=True)
            embed.add_field(name="🏆 전체 순위", value=f"**{rank:,}위**" if rank else "Unranked", inline=True)
            
            embed.add_field(name="✅ 푼 문제", value=f"**{solved:,}**개", inline=True)
            embed.add_field(name="🔥 최대 스트릭", value=f"**{streak:,}**일", inline=True)
            embed.add_field(name="🎓 클래스", value=f"Class **{user_class}**", inline=True)
            
            embed.set_footer(text="데이터 제공: Solved.ac")
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("프로필 정보를 불러오는 데 실패했습니다. 존재하지 않는 아이디일 수 있습니다.")

    # 3. /추천 (랜덤 5개)
    @app_commands.command(name="추천", description="조건에 맞는 한글 문제를 랜덤으로 추천해줍니다.")
    @app_commands.describe(difficulty="난이도", category="유형")
    async def recommend(self, interaction: discord.Interaction, difficulty: str, category: str):
        await interaction.response.defer()

        problems = search_problems(difficulty, category)

        if problems:
            # 1. 한글 제목이 있는 문제만 필터링
            ko_problems = [p for p in problems if p.get('titleKo')]

            if not ko_problems:
                await interaction.followup.send(f"❌ `{difficulty} + {category}` 조건의 한글 문제를 찾지 못했습니다.")
                return

            # 2. 핵심: 검색된 문제들 중 최대 5개를 랜덤하게 뽑습니다.
            selected_problems = random.sample(ko_problems, min(len(ko_problems), 5))
            count = len(selected_problems)
            embed = discord.Embed(
                title=f"🧩 추천 한글 문제 (랜덤 {count}개)",
                description=f"🔍 검색 조건: `{difficulty}`, `{category}`",
                color=discord.Color.gold()
            )

            # 3. 뽑힌 문제들만 루프를 돌며 추가
            for idx, problem in enumerate(selected_problems):
                title = problem['titleKo']
                pid = problem['problemId']
                level = problem['level']
                tags = [tag['key'] for tag in problem['tags']]
                url = f"https://www.acmicpc.net/problem/{pid}"       
                tier_name = TIER_DATA.get(level, "Unrated")

                embed.add_field(
                    name=f"{idx+1}. [{tier_name}] {title} ({pid}번)",
                    value=f"[문제 바로가기]({url}) | 🏷️ {', '.join(tags[:2])}",
                    inline=False
                )

            embed.set_footer(text="원하는 문제 번호를 복사해서 /공지 명령어를 사용하세요!")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ `{difficulty} + {category}` 조건에 맞는 문제가 없습니다.")

    # 4. /공지 (에러 해결 핵심 부분!)
    @app_commands.command(name="공지", description="스터디 문제를 공지합니다.")
    @app_commands.describe(기한="마감일 (예: 0316)", 문제1="문제 번호", 문제2="문제 번호 (선택)")
    async def announce(self, interaction: discord.Interaction, 기한: str, 문제1: str, 문제2: str = None):
        await interaction.response.defer()
        p_ids = [pid for pid in [문제1, 문제2] if pid and pid.isdigit()]
        
        today = datetime.now()
        
        # 1. '기한' 텍스트에서 날짜 추출 (0316, 3월16일 등 모두 대응)
        numbers = re.findall(r'\d+', 기한)
        try:
            if len(numbers) == 1 and len(numbers[0]) >= 3:
                num_str = numbers[0].zfill(4)
                month, day = int(num_str[:2]), int(num_str[2:])
            elif len(numbers) >= 2:
                month, day = int(numbers[0]), int(numbers[1])
            else:
                raise ValueError
                
            target_year = today.year
            if month < today.month: # 목표 월이 현재 월보다 작으면 내년으로 처리
                target_year += 1
            deadline_dt = datetime(target_year, month, day, 23, 59, 59)
        except:
            # 해석 실패 시 기본 3일 뒤 자정으로 설정
            deadline_dt = today + timedelta(days=3)
            
        deadline_str = deadline_dt.strftime("%Y-%m-%d %H:%M:%S")
        announced_date_str = today.strftime("%m/%d")
        
        # 2. 새로운 문제를 덮어씌우지 않고 누적 업데이트 (이미 있다면 기한만 연장)
        for pid in p_ids:
            existing_p = next((p for p in self.announced_problems if p['pid'] == pid), None)
            if existing_p:
                existing_p['deadline'] = deadline_str
                if 'announced_date' not in existing_p:
                    existing_p['announced_date'] = announced_date_str
            else:
                self.announced_problems.append({'pid': pid, 'deadline': deadline_str, 'announced_date': announced_date_str})
                
        self.save_data()
        
        description = []
        for i, pid in enumerate(p_ids):
            p_info = get_problem_by_id(int(pid))
            if p_info:
                title = p_info['titleKo']
                level = p_info['level']
                tier_name = TIER_DATA.get(level, "Unknown")
                
                # 태그 추출 (한글명 우선, 너무 길어지지 않게 최대 3개까지만 출력)
                tags = []
                for t in p_info.get('tags', []):
                    ko_tag = next((dn['name'] for dn in t.get('displayNames', []) if dn.get('language') == 'ko'), t.get('key', ''))
                    tags.append(ko_tag)
                tag_str = ", ".join(tags[:3]) if tags else "태그 없음"
                
                description.append(f"**{i+1}.** [{tier_name}] [{pid}. {title}](https://www.acmicpc.net/problem/{pid})\n> 🏷️ {tag_str}")
        
        embed = discord.Embed(title=f"📅 {today.strftime('%m/%d')} 📃오늘의 스터디 문제 공지 (~{기한})", description="\n\n".join(description), color=discord.Color.blue())
        msg = await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ 공지 완료!", ephemeral=True)
        for i in range(len(description)):
            await msg.add_reaction(["1️⃣", "2️⃣"][i])

    # 6. /랭킹 (스터디원 전체 순위)
    @app_commands.command(name="랭킹", description="스터디원들의 실력 순위를 확인합니다.")
    async def ranking(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.members:
            await interaction.followup.send("❌ 등록된 스터디원이 없습니다.")
            return

        rank_data = []
        for user_id, handle in self.members.items():
            info = get_user_info(handle)
            if info:
                rank_data.append({
                    'handle': handle,
                    'user_id': user_id,
                    'rating': info.get('rating', 0),
                    'streak': info.get('maxStreak', 0),
                    'solved': info.get('solvedCount', 0),
                    'tier': info.get('tier', 0)
                })

        # 레이팅 기준 내림차순 정렬
        rank_data.sort(key=lambda x: x['rating'], reverse=True)

        embed = discord.Embed(title="🏆 스터디 실력 랭킹", color=discord.Color.gold())
        
        for i, data in enumerate(rank_data):
            member = interaction.guild.get_member(data['user_id'])
            name = member.display_name if member else data['handle']
            tier_name = TIER_DATA.get(data['tier'], "Unknown")
            
            rank_line = f"[{tier_name}] **{data['rating']}점** | 🔥 {data['streak']}일 | ✅ {data['solved']}문제"
            embed.add_field(name=f"{i+1}위. {name} ({data['handle']})", value=rank_line, inline=False)

        await interaction.followup.send(embed=embed)


    # 7. /문제뽑기 [난이도]
    @app_commands.command(name="문제뽑기", description="지정한 난이도의 문제를 랜덤으로 5개 뽑아줍니다.")
    @app_commands.describe(difficulty="난이도 (예: 골드5, 실버1)")
    async def extract_problems(self, interaction: discord.Interaction, difficulty: str):
        await interaction.response.defer()
        
        problems = search_problems(difficulty, "")

        if problems:
            # 1. 일단 한글 제목이 있는 문제들을 다 모읍니다.
            ko_problems = [p for p in problems if p.get('titleKo')]
            
            if not ko_problems:
                await interaction.followup.send(f"❌ `{difficulty}` 난이도의 한글 문제를 찾지 못했습니다.")
                return

            # 2. 전체 목록에서 랜덤하게 5개를 뽑습니다.
            # min(len(ko_problems), 5)는 문제가 5개보다 적을 경우를 대비한 안전장치입니다.
            selected_problems = random.sample(ko_problems, min(len(ko_problems), 5))

            count = len(selected_problems)
            embed = discord.Embed(
                title=f"🎲 랜덤 문제 뽑기 (총 {count}개)",
                description=f"🎯 선택 난이도: `{difficulty}`",
                color=discord.Color.purple()
            )

            # 3. 뽑힌(selected_problems) 문제들로 필드를 만듭니다.
            for idx, problem in enumerate(selected_problems):
                title = problem['titleKo']
                pid = problem['problemId']
                level = problem['level']
                tags = [tag['key'] for tag in problem['tags']]
                url = f"https://www.acmicpc.net/problem/{pid}"
                
                tier_name = TIER_DATA.get(level, "Unrated")
                tag_display = f"🏷️ {', '.join(tags[:2])}" if tags else "🏷️ 태그 없음"
                
                embed.add_field(
                    name=f"{idx+1}. [{tier_name}] {title} ({pid}번)",
                    value=f"[문제 바로가기]({url}) | {tag_display}",
                    inline=False
                )
            
            embed.set_footer(text="뽑힌 문제 번호를 복사해서 /공지 명령어로 등록해 보세요!")
            await interaction.followup.send(embed=embed)


    
    # 8. /검색 [문제번호]
    @app_commands.command(name="검색", description="특정 문제 번호의 상세 정보를 조회합니다.")
    @app_commands.describe(problem_id="문제 번호 (예: 1000)")
    async def search_problem(self, interaction: discord.Interaction, problem_id: int):
        await interaction.response.defer()
        p_info = get_problem_by_id(problem_id)
        
        if p_info:
            title = p_info['titleKo']
            level = p_info['level']
            
            # 태그 추출 (한글명 우선)
            tags = []
            for t in p_info.get('tags', []):
                ko_tag = next((dn['name'] for dn in t.get('displayNames', []) if dn.get('language') == 'ko'), t.get('key', ''))
                tags.append(ko_tag)
                
            url = f"https://www.acmicpc.net/problem/{problem_id}"
            
            tier_name = TIER_DATA.get(level, "Unrated")
            tag_str = ", ".join(tags[:5]) if tags else "태그 없음"
            
            embed = discord.Embed(
                title=f"🔍 [{tier_name}] {title} ({problem_id}번)",
                url=url,
                color=discord.Color.teal()
            )
            embed.add_field(name="알고리즘 분류", value=f"🏷️ {tag_str}", inline=False)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ `{problem_id}`번 문제를 찾을 수 없습니다.")

    # 9. /알림채널설정
    @app_commands.command(name="알림채널설정", description="밤 9시 알림 채널 지정")
    async def set_alert_channel(self, interaction: discord.Interaction):
        self.alert_channel_id = interaction.channel_id
        self.save_data() # 저장!
        if not self.daily_alert.is_running():
            self.daily_alert.start()
        await interaction.response.send_message("✅ 알림 채널 설정 완료!")

    # 10. 밤 9시 알림
    @tasks.loop(time=time(hour=21, minute=0, tzinfo=timezone(timedelta(hours=9))))
    async def daily_alert(self):
        if self.alert_channel_id:
            channel = self.bot.get_channel(int(self.alert_channel_id))
            if channel:
                await channel.send("🔔 **밤 9시입니다! '1일 1solve!' 실천합시다!**\n**Study 공지 문제가 어렵다고 느껴지시면 다른 쉬운 문제 하나라도 풀어볼까요?**")

    @daily_alert.before_loop
    async def before_daily_alert(self):
        await self.bot.wait_until_ready()

    # 11. /알림해제
    @app_commands.command(name="알림해제", description="설정된 밤 9시 생존 알림을 취소합니다.")
    async def stop_alert(self, interaction: discord.Interaction):
        # 1. 기억하고 있는 채널 ID 삭제
        self.alert_channel_id = None
        
        # 2. 실행 중인 타이머가 있다면 중지
        if self.daily_alert.is_running():
            self.daily_alert.stop()
            
        # 3. 만약 파일 저장 기능을 쓰고 있다면 저장 함수도 호출 (선택)
        self.save_data() 

        await interaction.response.send_message("📴 밤 9시 생존 확인 알림이 해제되었습니다. 다시 설정하려면 `/알림채널설정`을 사용하세요!", ephemeral=False)

    # 11-2. /풀이알림채널설정 (새로운 명령어)
    @app_commands.command(name="풀이알림채널설정", description="스터디원들이 문제를 풀었을 때 알림을 전송할 전용 채널을 지정합니다.")
    async def set_solve_alert_channel(self, interaction: discord.Interaction):
        self.solve_alert_channel_id = interaction.channel_id
        self.save_data()
        if not self.check_solutions.is_running():
            self.check_solutions.start()
        await interaction.response.send_message("✅ 풀이 알림(감지) 채널 설정 완료!")

    # 13. /도움말
    @app_commands.command(name="도움말", description="봇에서 사용할 수 있는 모든 명령어와 설명을 확인합니다.")
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🤖 스터디 봇 명령어 안내",
            description="현재 봇에서 사용할 수 있는 전체 명령어 목록입니다.",
            color=discord.Color.green()
        )
        
        # 이 Cog(Study 클래스)에 등록된 모든 슬래시 명령어를 자동으로 가져와서 임베드에 추가합니다.
        for cmd in self.get_app_commands():
            embed.add_field(name=f"/{cmd.name}", value=cmd.description, inline=False)
            
        embed.set_footer(text="💡 새로운 명령어가 추가 시 업데이트됩니다.")
        await interaction.followup.send(embed=embed)

    # 14. /아이디 (등록된 스터디원 목록)
    @app_commands.command(name="아이디", description="봇에 등록된 스터디원들의 백준 아이디 목록을 확인합니다.")
    async def show_members_id(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not self.members:
            await interaction.followup.send("❌ 등록된 스터디원이 없습니다.")
            return
            
        embed = discord.Embed(
            title="👥 등록된 스터디원 아이디 목록",
            color=discord.Color.green()
        )
        
        description_lines = []
        for user_id, handle in self.members.items():
            if interaction.guild:
                member = interaction.guild.get_member(user_id)
                if not member:
                    try:
                        member = await interaction.guild.fetch_member(user_id)
                    except discord.HTTPException:
                        member = None
            else:
                member = None
                
            name = member.display_name if member else "알 수 없는 유저"
            description_lines.append(f"👤 **{name}** : [{handle}](https://solved.ac/profile/{handle})")
            
        embed.description = "\n\n".join(description_lines)
        await interaction.followup.send(embed=embed)

    # 12. 5분마다 실행되는 풀이 감지기
    @tasks.loop(minutes=5)
    async def check_solutions(self):
        # 1. 기한이 지난 문제 자동으로 목록에서 정리
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        valid_problems = [p for p in self.announced_problems if p.get('deadline', '') >= now_str]
        
        if len(self.announced_problems) != len(valid_problems):
            self.announced_problems = valid_problems
            self.save_data()

        # 2. 감지할 문제가 없거나, 알림 채널이 설정 안 되어있으면 종료
        if not self.announced_problems or not self.solve_alert_channel_id:
            return

        # 풀이 알림 전용 채널 사용
        channel = self.bot.get_channel(int(self.solve_alert_channel_id))
        if not channel:
            return
            
        active_pids = [p['pid'] for p in self.announced_problems]
        if not active_pids:
            return
            
        # 검색어 생성: s@유저명 (id:1000 | id:1001) 형태로 '공지된 문제들'만 정확히 필터링
        ids_query = " | ".join([f"id:{pid}" for pid in active_pids])

        for user_id, handle in self.members.items():
            try:
                query_str = f"s@{handle} ({ids_query})"   
                res = requests.get("https://solved.ac/api/v3/search/problem", params={"query": query_str}, timeout=5)
                if res.status_code == 200:
                    user_solved = [str(item['problemId']) for item in res.json().get('items', [])]
                    
                    for pid in active_pids:
                        if pid in user_solved and pid not in self.solved_log.get(user_id, {}):
                            member = channel.guild.get_member(user_id)
                            name = member.display_name if member else handle
                            
                            # 공지일 정보 가져오기
                            target_p = next((p for p in self.announced_problems if p['pid'] == pid), {})
                            ann_date = target_p.get('announced_date')
                            date_prefix = f"'{ann_date} 공지문제' " if ann_date else "공지된 "
                            
                            await channel.send(f"✅ **{name}**님이 {date_prefix}**{pid}번** 문제를 해결했습니다!")
                            
                            if user_id not in self.solved_log:
                                self.solved_log[user_id] = {}
                            
                            # 데이터가 리스트인 경우와 딕셔너리인 경우 모두 안전하게 처리
                            if isinstance(self.solved_log[user_id], list):
                                self.solved_log[user_id].append(pid)
                            else:
                                self.solved_log[user_id][str(pid)] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                            self.save_data()
            except Exception as e:
                print(f"[{handle}] 풀이 확인 중 에러 발생: {e}")
                continue

    @check_solutions.before_loop
    async def before_check_solutions(self):
        await self.bot.wait_until_ready()

    # 13. 10분마다 실행되는 티어/클래스 상승 감지기
    @tasks.loop(minutes=10)
    async def check_user_stats(self):
        # 알림 채널이 설정 안 되어있으면 종료
        if not self.solve_alert_channel_id:
            return

        channel = self.bot.get_channel(int(self.solve_alert_channel_id))
        if not channel:
            return

        for user_id, handle in self.members.items():
            user_info = get_user_info(handle)
            if not user_info:
                continue
                
            new_tier = user_info.get('tier', 0)
            new_class = user_info.get('class', 0)
            
            if user_id not in self.user_stats:
                self.user_stats[user_id] = {'tier': new_tier, 'class': new_class}
                self.save_data()
                continue
                
            old_stats = self.user_stats[user_id]
            old_tier = old_stats.get('tier', new_tier)
            old_class = old_stats.get('class', new_class)
            
            updates_made = False
            member = channel.guild.get_member(user_id)
            name = member.display_name if member else handle
            
            if new_tier > old_tier:
                old_tier_name = TIER_DATA.get(old_tier, "Unknown")
                new_tier_name = TIER_DATA.get(new_tier, "Unknown")
                embed = discord.Embed(title="🎉 티어 승급을 축하합니다!", description=f"**{name}**({handle})님이 **{new_tier_name}**(으)로 승급하셨습니다!\n(이전 티어: {old_tier_name})", color=discord.Color.green())
                await channel.send(embed=embed)
                old_stats['tier'] = new_tier
                updates_made = True
                
            if new_class > old_class:
                embed = discord.Embed(title="🎓 클래스 승급을 축하합니다!", description=f"**{name}**({handle})님이 **Class {new_class}**(으)로 승급하셨습니다!\n(이전 클래스: Class {old_class})", color=discord.Color.gold())
                await channel.send(embed=embed)
                old_stats['class'] = new_class
                updates_made = True
                
            if updates_made:
                self.user_stats[user_id] = old_stats
                self.save_data()

    @check_user_stats.before_loop
    async def before_check_user_stats(self):
        await self.bot.wait_until_ready()

    # 15. /문제풀이현황
    @app_commands.command(name="문제풀이현황", description="주간, 월간, 누적 공지문제 풀이 개수를 확인합니다.")
    async def solve_status(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.members:
            await interaction.followup.send("❌ 등록된 스터디원이 없습니다.")
            return

        now = datetime.now()
        # 주간 기준: 이번 주 월요일 00:00:00
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 월간 기준: 이번 달 1일 00:00:00
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        embed = discord.Embed(
            title="📊 공지문제 풀이 현황",
            description=f"기준일: {now.strftime('%Y년 %m월 %d일')}",
            color=discord.Color.blue()
        )

        # 멤버별 통계 계산
        stats = []
        for user_id, handle in self.members.items():
            solved_data = self.solved_log.get(user_id, {})
            
            weekly_count = 0
            monthly_count = 0
            total_count = len(solved_data)

            for pid, solved_time_str in solved_data.items():
                try:
                    solved_time = datetime.strptime(solved_time_str, "%Y-%m-%d %H:%M:%S")
                    if solved_time >= start_of_week:
                        weekly_count += 1
                    if solved_time >= start_of_month:
                        monthly_count += 1
                except ValueError:
                    # 날짜 형식이 안 맞거나 옛날 구버전 데이터면 누적에만 포함시킵니다.
                    pass

            if interaction.guild:
                member = interaction.guild.get_member(user_id)
                if not member:
                    try:
                        member = await interaction.guild.fetch_member(user_id)
                    except discord.HTTPException:
                        member = None
            else:
                member = None
                
            name = member.display_name if member else "알 수 없는 유저"

            stats.append({'name': name, 'handle': handle, 'weekly': weekly_count, 'monthly': monthly_count, 'total': total_count})

        # 누적 푼 문제가 많은 순서대로 정렬 (누적이 같으면 주간 푼 문제 순)
        stats.sort(key=lambda x: (x['total'], x['weekly']), reverse=True)

        for i, s in enumerate(stats):
            embed.add_field(name=f"{i+1}. {s['name']} ({s['handle']})", value=f"주간: **{s['weekly']}**개 | 월간: **{s['monthly']}**개 | 누적: **{s['total']}**개", inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
