import os
from dotenv import load_dotenv

load_dotenv()

# 런타임 비밀값은 환경변수에서 읽어 와 코드와 설정을 분리한다.
TOKEN = os.getenv("DISCORD_TOKEN")

# 선택값은 기본값을 둬서 환경변수가 비어 있어도 초기화가 깨지지 않게 한다.
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

# 외부 API 엔드포인트는 상수로 고정해 호출 지점을 한 곳에서 관리한다.
SOLVED_AC_API_URL = "https://solved.ac/api/v3"

# 명령 접두사는 설정값으로 분리해 운영 중에도 쉽게 바꿀 수 있게 둔다.
COMMAND_PREFIX = "!"
