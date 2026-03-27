# Discord Algorithm Study Bot (AlgoBot)

> **"스터디 운영의 병목 현상을 자동화로 해결한 맞춤형 알고리즘 서포터"**

알고리즘 스터디 운영 중 발생한 **비효율적인 문제 선정 과정**과 **낮은 접근성**을 해결하기 위해 개발된 Discord 전용 봇입니다. Solved.ac API를 활용하여 정밀한 문제 추천 및 공지 자동화 기능을 제공합니다.

-----

## Tech Stack

  * **Language:** Python
  * **API:** [Solved.ac API v3](https://solved.ac/api/v3)
  * **Infra:** `JSON` (Data Persistence)

-----

## Key Problems & Solutions

### 1\. 정밀한 문제 추천의 부재 (Custom Recommendation)

  * **Problem:** 기존 봇들은 세부 난이도나 유형별 필터링이 부족하여, 스터디원의 수준에 맞는 문제를 찾는 데 시간이 많이 소요됨.
  * **Solution:** `Solved.ac API`의 쿼리 파라미터를 분석하여 **[난이도(Tier) + 알고리즘 태그(Tag)]** 조합 검색 기능을 구현했습니다.
  * **Result:** "실버 1 수준의 BFS 문제"와 같이 팀의 학습 목표에 직결되는 문제를 1초 만에 추천받을 수 있게 되었습니다.

### 2\. 수동 공지 방식의 번거로움 (Automation)

  * **Problem:** 문제 선정 후 링크 복사, 날짜 기입, 투표 생성 등 반복적인 수동 작업이 발생함.
  * **Solution:** Slash Command(`  /공지 `) 하나로 **문제 제목, 백준(BOJ) 다이렉트 링크, 마감 기한, 투표 이모지**가 포함된 정형화된 템플릿을 자동 생성합니다.
  * **Result:** 공지 작성 시간을 60% 이상 단축하고, 멤버들의 문제 접근성을 극대화했습니다.

### 3\. 문제풀이 확인의 번거로움
  * **Problem:** 스터디원 별 공지 문제풀이 현황을 파악의 번거로움 및 주간, 월간, 누적 집계 필요성 발생함.
  * **Solution:** 5분마다 API 호출을 통해 문제풀이 현황을 파악하고, 공지문제 풀이 시 알람채널에 알람 발송, 집계 리스트에 count +1로 파악 및 집계 자동화하였습니다.
  * **Result:** 문제풀이 현황 파악 시간을 90%이상 단축하고, 스터디원 문제풀이 현황 집계 시각화를 통해 동기부여하였습니다.

-----

## Architecture & Design

  * **Cogs (Modularization):** 기능별로 명령어를 분리하여 유지보수성을 높였습니다. (`study.py`, `profile.py` 등)
  * **Data Persistence:** 봇 리부팅 시에도 사용자 연동 정보가 유지되도록 `JSON` 기반의 데이터 저장 로직을 설계했습니다.
  * **Notification System:** 매일 저녁 9시, `Cron` 방식의 스케줄러를 통해 스터디 참여를 독려하는 알림 시스템을 구축했습니다.

-----

## Learning Points

  * **API 활용 능력:** 외부 API 문서(Solved.ac)를 분석하고, 효율적인 쿼리를 작성하는 능력을 배양했습니다.
  * **사용자 중심 개발:** 내가 겪은 불편함이 곧 팀의 불편함이라는 점을 인지하고, 실질적인 솔루션을 제안하는 경험을 쌓았습니다.
  * **비동기 프로그래밍:** 봇의 반응 속도를 최적화하기 위해 비동기 통신 구조를 이해하고 적용했습니다.

-----

## License & Credit

  * **Problem Data:** [Solved.ac](https://solved.ac/)

-----

<details>
<summary>배포 가이드</summary>


하다가 막히는 부분이 있으면 생성형 AI를 활용하기 바랍니다.

-----

## 🔑 1단계: 디스코드 봇 신분증(토큰) 발급받기

가장 먼저 봇이 디스코드에 접속할 수 있는 '비밀번호(토큰)'를 받아야 합니다.

1.  [디스코드 개발자 포털](https://discord.com/developers/applications)에 접속해 로그인합니다.
2.  우측 상단의 **[New Application]** 을 누르고 봇 이름(예: BearBot)을 적어 생성합니다.
3.  왼쪽 메뉴에서 **[Bot]** 탭을 클릭합니다.
4.  **Privileged Gateway Intents** 항목을 찾아서 **3개의 스위치를 모두 파란색(ON)** 으로 켭니다. (봇이 채팅을 읽으려면 꼭 필요해요\!)
5.  위쪽의 **[Reset Token]** 버튼을 눌러 **토큰(Token)** 을 발급받습니다.
    > 🚨 **절대 주의:** 이 토큰은 봇의 심장입니다. 절대 깃허브나 단톡방에 올리지 마세요\! 일단 **메모장에 안전하게 복사**해 둡니다.

## 🤝 2단계: 우리 서버에 봇 초대하기

1.  왼쪽 메뉴에서 \*\*[OAuth2] -\> [https://www.homedepot.com/b/Outdoors-Outdoor-Power-Equipment-Generators/N-5yc1vZbx8l\*\*를](https://www.google.com/search?q=https://www.homedepot.com/b/Outdoors-Outdoor-Power-Equipment-Generators/N-5yc1vZbx8l**%EB%A5%BC) 클릭합니다.
2.  **Scopes** 체크박스에서 `bot`과 `applications.commands` 두 개를 체크합니다.
3.  아래에 나타나는 **Bot Permissions**에서 `Administrator(관리자)`를 체크합니다.
4.  맨 아래에 생성된 **긴 URL을 복사해서 인터넷 창에 붙여넣기** 한 뒤, 우리 스터디 서버를 선택해 봇을 초대합니다.

-----

## ☁️ 3단계: Oracle Cloud 서버(컴퓨터) 대여하기

봇이 24시간 켜져 있으려면 꺼지지 않는 컴퓨터(서버)가 필요합니다.

1.  오라클 클라우드에 접속하여 \*\*[인스턴스 생성 (Create Instance)]\*\*을 누릅니다.
2.  **이미지 및 구성 (Image and Shape):** - 이미지: `Ubuntu 22.04` (또는 24.04)
      - 구성(Shape): `VM.Standard.E2.1.Micro` (항상 무료 등급)
3.  **SSH 키 추가 (Add SSH keys):**
      - **[전용 키 저장(Save private key)]** 버튼을 눌러 `.key` 파일을 꼭 다운로드하세요\! (서버 접속용 유일한 열쇠입니다.)
4.  인스턴스를 생성하고, 화면에 \*\*퍼블릭 IP(Public IP)\*\*가 뜨면 메모장에 복사해 둡니다.

---

## 💻 4단계: 까만 화면(서버)에 접속하기
이제 내 PC에서 클라우드 서버로 원격 접속을 해봅시다. 윈도우 환경을 기준으로 설명합니다.

1. **터미널(PowerShell 또는 Git Bash)**을 엽니다.
2. 다운받은 `.key` 파일의 **절대 경로**를 복사합니다. (파일 우클릭 -> '경로 복사')
3. 아래 명령어 양식에 맞춰 입력 후 엔터를 칩니다. 
   
   **[명령어 양식]**
   ```bash
   ssh -i "내_열쇠의_절대경로.key" ubuntu@오라클_퍼블릭IP
   ```
   **[실제 입력 예시]**
   ```bash
   ssh -i "F:\GitHub\Discord_Algorthms_StudyBot\ssh-key-2026-02-17.key" ubuntu@129.154.58.149
   ```
   * *Are you sure you want to continue connecting (yes/no/[fingerprint])? 라고 물으면 `yes`를 치고 엔터를 누릅니다.*

---

## ⚙️ 5단계: 서버 기본 세팅 및 코드 가져오기
접속에 성공했다면, `ubuntu@...` 처럼 초록색 글씨가 뜹니다. 이제 봇을 돌릴 환경을 설치해 봅시다.

**1) 앱스토어 업데이트 및 파이썬 설치**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

**2) 깃허브에서 봇 소스코드 가져오기 및 폴더 이동**
```bash
git clone https://github.com/내계정/Discord_Algorthms_StudyBot.git
cd ~/Discord_Algorthms_StudyBot
```

---

## 📦 6단계: 가상환경 활성화 및 필수 패키지 설치
여기서부터가 진짜 중요합니다! 봇 구동에 필요한 부품들을 설치합니다.

**1. 가상환경 활성화 (이미 되어 있다면 패스)**
```bash
# 봇 전용 격리 공간을 만들고 들어갑니다.
python3 -m venv venv
source venv/bin/activate
```
*(성공하면 터미널 줄 맨 앞에 `(venv)` 가 생깁니다!)*

**2. 필수 패키지 설치 (dotenv 주의!)**
```bash
pip install --upgrade pip
pip install discord.py requests pandas

# 🚨 주의: 패키지 이름은 'python-dotenv' 입니다! (봇 에러의 주범!)
pip install python-dotenv
```

---

## 🤫 7단계: 비밀번호 상자(.env) 만들기
토큰을 안전하게 보관할 `.env` 파일을 서버에 직접 만들어줍니다.

1. 메모장(nano)을 엽니다.
   ```bash
   nano .env
   ```
2. 까만 화면이 열리면 아래 내용을 적습니다. (발급받은 디스코드 토큰을 넣으세요!)
   ```env
   DISCORD_TOKEN=여기에_진짜_토큰을_붙여넣기하세요
   ```
3. **저장하고 나가는 방법:**
   - `Ctrl + O` 누르기 (저장 단축키) -> `Enter` 치기 -> `Ctrl + X` 누르기 (종료 단축키)

---

## 🏃‍♂️ 8단계: 설치 확인 후 봇 실행 테스트!
준비가 다 되었습니다. 심호흡을 하고 봇을 켜봅시다.
```bash
python3 main.py
```
화면에 **"Logged in as (봇 이름)"** 라는 말이 뜨고, 디스코드 서버에 봇이 온라인으로 나타나면 대성공입니다! 🎉

확인했다면 **`Ctrl + C`**를 눌러서 봇을 잠시 꺼주세요. (터미널을 끄면 봇이 죽어버리기 때문에, 24시간 돌아가게 하는 마지막 세팅을 해야 합니다.)

---

## 🔋 9단계: 24시간 무중단 실행 모드 (systemd)
내가 노트북을 끄고 퇴근해도 서버에서 봇이 계속 일하도록 관리자에게 맡기는 작업입니다.

1. 관리자 설정 파일을 엽니다.
   ```bash
   sudo nano /etc/systemd/system/bearbot.service
   ```
2. 아래 내용을 그대로 복사해서 붙여넣습니다.
   ```ini
   [Unit]
   Description=Algo Bandit BearBot Service
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/Discord_Algorthms_StudyBot
   Environment="PATH=/home/ubuntu/Discord_Algorthms_StudyBot/venv/bin"
   ExecStart=/home/ubuntu/Discord_Algorthms_StudyBot/venv/bin/python main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   *(저장: `Ctrl+O` -> `Enter` -> `Ctrl+X`)*

3. 봇 자동 실행 시작! (한 줄씩 실행)
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bearbot
   sudo systemctl start bearbot
   ```

4. 봇이 잘 돌아가는지 상태 확인
   ```bash
   sudo systemctl status bearbot
   ```
   초록색으로 **`active (running)`** 이라고 떠 있다면, 이제 터미널 창을 닫으셔도 됩니다!

-----

#### 🚨 에러가 발생했다면 생성형 AI를 활용하기 바랍니다.

-----




</details>
