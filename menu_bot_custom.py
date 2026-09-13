import os
import subprocess
import requests
from datetime import datetime

# ========== 설정 ==========
STORES = [
    {"name": "교직원 공제회",  "type": "cjfreshmeal", "id": 6848,        "url": "https://front.cjfreshmeal.co.kr/main"},
    {"name": "FKI 타워",      "type": "cjfreshmeal", "id": 6083,        "url": "https://front.cjfreshmeal.co.kr/main"},
    {"name": "IFC 서울",      "type": "welstory",    "id": "REST000100","url": "https://welplan.pmh.codes/restaurants/welstory/REST000100/ifc%EC%84%9C%EC%9A%B8"},
]
HTML_FILE = "index.html"
# ==========================


def get_cjfreshmeal_menu(store_id, date):
    url = (
        "https://front.cjfreshmeal.co.kr/meal/v1/today-all-meal"
        f"?storeIdx={store_id}&mealDt={date}&reqType=main"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://front.cjfreshmeal.co.kr/",
    }
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    data = res.json()
    if data.get("status") != "success":
        return []
    result = []
    for item in data.get("data", {}).get("2", []):
        result.append({
            "name":   item.get("name")   or "",
            "side":   item.get("side")   or "",
            "kcal":   item.get("kcal")   or 0,
            "corner": item.get("corner") or "",
        })
    return result


def get_welstory_menu(restaurant_id, date):
    url = (
        "https://welplan.pmh.codes/api/menu/live"
        f"?kind=gallery&date={date}&time=all&restaurantId={restaurant_id}"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://welplan.pmh.codes/",
    }
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    data = res.json()
    result = []
    for item in data.get("menus", []):
        if str(item.get("mealTimeId")) != "2":
            continue
        components = item.get("components", [])
        side_items = [c["name"] for c in components if not c.get("isMain")]
        result.append({
            "name":   item.get("name") or "",
            "side":   ", ".join(side_items),
            "kcal":   item.get("nutrition", {}).get("calories") or 0,
            "corner": "",
        })
    return result


def fetch_all_menus(date):
    all_menus = []
    for store in STORES:
        try:
            if store["type"] == "cjfreshmeal":
                items = get_cjfreshmeal_menu(store["id"], date)
            elif store["type"] == "welstory":
                items = get_welstory_menu(store["id"], date)
            else:
                items = []
            all_menus.append({"name": store["name"], "items": items, "url": store.get("url", "")})
            print(f"[OK] {store['name']} 메뉴 {len(items)}개 수집")
        except Exception as e:
            print(f"[ERROR] {store['name']}: {e}")
            all_menus.append({"name": store["name"], "items": [], "url": store.get("url", "")})
    return all_menus


def generate_html(all_menus, date):
    today_label = datetime.strptime(date, "%Y%m%d").strftime("%Y년 %m월 %d일")

    cards = ""
    for store in all_menus:
        items_html = ""
        if not store["items"]:
            items_html = '<p class="no-menu">메뉴 정보 없음</p>'
        else:
            for item in store["items"]:
                corner = f'<span class="corner">[{item["corner"]}]</span> ' if item["corner"] else ""
                side   = f'<p class="side">{item["side"]}</p>' if item["side"] else ""
                items_html += f"""
                <div class="menu-item">
                    <div class="menu-name">{corner}{item['name']}
                        <span class="kcal">{item['kcal']} kcal</span>
                    </div>
                    {side}
                </div>"""

        url      = store.get("url", "")
        link_btn = f'<a class="link-btn" href="{url}" target="_blank">🔗 메뉴 사이트 바로가기</a>' if url else ""

        cards += f"""
        <div class="card">
            <h2>📍 {store['name']}</h2>
            {items_html}
            {link_btn}
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>점심 메뉴 - {today_label}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        header {{
            text-align: center;
            padding: 20px 0 30px;
        }}
        header h1 {{ font-size: 1.6rem; color: #333; }}
        header p  {{ color: #888; margin-top: 6px; font-size: 0.9rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card h2 {{
            font-size: 1rem;
            color: #444;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .menu-item  {{ margin-bottom: 12px; }}
        .menu-name  {{ font-size: 0.95rem; color: #222; font-weight: 500; }}
        .corner     {{ color: #0078d4; font-size: 0.85rem; }}
        .kcal       {{ color: #888; font-size: 0.8rem; font-weight: 400; }}
        .side       {{ font-size: 0.82rem; color: #999; margin-top: 3px; }}
        .no-menu    {{ color: #bbb; font-size: 0.9rem; }}
        .link-btn   {{
            display: inline-block;
            margin-top: 12px;
            padding: 6px 12px;
            background: #f0f4ff;
            color: #0078d4;
            border-radius: 6px;
            font-size: 0.82rem;
            text-decoration: none;
        }}
        .link-btn:hover {{ background: #dce8ff; }}
        footer {{
            text-align: center;
            margin-top: 30px;
            color: #bbb;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🍽️ {today_label} 점심 메뉴</h1>
        <p>SAP Korea 주변 구내식당</p>
    </header>
    <div class="grid">
        {cards}
    </div>
    <footer>매일 오전 11시 업데이트</footer>
</body>
</html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] index.html 생성 완료 ({today_label})")


if __name__ == "__main__":
    today = datetime.now().strftime("%Y%m%d")
    print(f"점심 메뉴 수집 중... ({today})")

    all_menus = fetch_all_menus(today)
    generate_html(all_menus, today)

    try:
        subprocess.run(["git", "add", "index.html"], check=True)
        subprocess.run(["git", "commit", "-m", f"메뉴 업데이트 {today}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[OK] GitHub push 완료")
    except subprocess.CalledProcessError:
        print("[SKIP] 변경사항 없음")
