import requests
import random
from config import SOLVED_AC_API_URL
import time

# 1. 난이도 매핑 (유저 입력 -> Solved.ac Tier ID)
# 브론즈: 1~5, 실버: 6~10, 골드: 11~15, 플래티넘: 16~20
TIER_MAP = {
    # 브론즈
    "브론즈5": 1, "브5": 1, "b5": 1,
    "브론즈4": 2, "브4": 2, "b4": 2,
    "브론즈3": 3, "브3": 3, "b3": 3,
    "브론즈2": 4, "브2": 4, "b2": 4,
    "브론즈1": 5, "브1": 5, "b1": 5,
    # 실버
    "실버5": 6, "실5": 6, "s5": 6,
    "실버4": 7, "실4": 7, "s4": 7,
    "실버3": 8, "실3": 8, "s3": 8,
    "실버2": 9, "실2": 9, "s2": 9,
    "실버1": 10, "실1": 10, "s1": 10,
    # 골드
    "골드5": 11, "골5": 11, "g5": 11,
    "골드4": 12, "골4": 12, "g4": 12,
    "골드3": 13, "골3": 13, "g3": 13,
    "골드2": 14, "골2": 14, "g2": 14,
    "골드1": 15, "골1": 15, "g1": 15,
    # 플래티넘 (필요시 추가)
    "플래티넘5": 16, "플5": 16, "p5": 16,
}

# 2. 알고리즘 유형 매핑 (자주 쓰는 것 위주)
# 자주 사용하는 알고리즘 한글 키워드 -> Solved.ac 공식 태그 키
TAG_MAP = {
    # 기초 및 탐색
    "구현": "implementation",
    "시뮬레이션": "simulation",
    "브루트포스": "bruteforcing",
    "완전탐색": "bruteforcing",
    "그리디": "greedy",
    "탐욕법": "greedy",
    "정렬": "sorting",
    
    # 그래프 및 탐색
    "그래프": "graphs",
    "BFS": "bfs",
    "DFS": "dfs",
    "너비우선탐색": "bfs",
    "깊이우선탐색": "dfs",
    "다익스트라": "dijkstra",
    "데이크스트라": "dijkstra",
    "최단경로": "shortest_path",
    "플로이드": "floyd_warshall",
    "위상정렬": "topological_sorting",
    "MST": "mst",
    "최소스패닝트리": "mst",
    "유니온파인드": "disjoint_set",
    "분리집합": "disjoint_set",
    
    # 자료구조
    "자료구조": "data_structures",
    "스택": "stack",
    "큐": "queue",
    "우선순위큐": "priority_queue",
    "해시": "hash_set",
    "트리": "trees",
    "세그먼트트리": "segment_tree",
    
    # 동적계획법 및 수학
    "DP": "dp",
    "디피": "dp",
    "동적계획법": "dp",
    "수학": "math",
    "정수론": "number_theory",
    "소수": "primality_test",
    "기하학": "geometry",
    
    # 기타 빈출 유형
    "이분탐색": "binary_search",
    "이진탐색": "binary_search",
    "투포인터": "two_pointer",
    "슬라이딩윈도우": "sliding_window",
    "누적합": "prefix_sum",
    "백트래킹": "backtracking",
    "재귀": "recursion",
    "문자열": "string",
    "비트마스킹": "bitmask"
}

def get_user_info(handle: str):
    """(기존 함수 유지)"""
    url = f"{SOLVED_AC_API_URL}/user/show"
    headers = {"Content-Type": "application/json"}
    params = {"handle": handle}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def search_problems(tier_query, tag_query):
    """조건에 맞는 한글 문제를 검색하여 최대 10개 반환합니다."""
    
    tier_val = TIER_MAP.get(tier_query, None)
    tag_key = TAG_MAP.get(tag_query, tag_query)

    query_parts = []
    
    # 1. 난이도 쿼리
    if tier_val:
        query_parts.append(f"tier:{tier_val}")
    elif str(tier_query).isdigit():
        query_parts.append(f"tier:{tier_query}")

    # 2. 태그 쿼리
    if tag_key:
        query_parts.append(f"tag:{tag_key}")

    # 3. ✅ 한글 문제 필터 추가 (lang:ko)
    query_parts.append("lang:ko")

    # 랜덤 정렬 조합
    full_query = " ".join(query_parts) + " sort:random"
    
    url = f"{SOLVED_AC_API_URL}/search/problem"
    params = {
        "query": full_query,
        "direction": "asc",
        "page": 1,
        "c": random.randint(1, 1000000) # CDN 캐시(기억)를 우회하기 위한 무작위 더미 값
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['count'] > 0:
                return data['items'] # 10개 제한을 풀고 50개 전체를 반환
            else:
                return None
        return None
    except Exception as e:
        print(f"Search Error: {e}")
        return None

# 예시: utils/solvedac.py 내부
def get_problem_by_id(problem_id):
    url = f"https://solved.ac/api/v3/problem/show?problemId={problem_id}"
    # 🛑 timeout=5 를 넣어야 서버가 응답 없을 때 5초 뒤에 포기하고 다음으로 넘어갑니다.
    response = requests.get(url, timeout=5) 
    if response.status_code == 200:
        return response.json()
    return None