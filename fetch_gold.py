"""
매일 GitHub Actions가 이 스크립트를 실행해서
1) 국제 금시세(USD/oz) - metals-api.com (무료 API 키 필요)
2) 원/달러 환율 - frankfurter.app (키 불필요, ECB 기준환율)
를 가져와 data/history.json 에 하루 1건씩 누적 저장합니다.
"""
import os
import json
import datetime
import urllib.request

OZ_TO_GRAM = 31.1034768
HISTORY_PATH = "data/history.json"
KEEP_DAYS = 180


def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "gold-price-bot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def fetch_gold_usd_per_oz():
    api_key = os.environ["METALS_API_KEY"]
    url = f"https://metals-api.com/api/latest?access_key={api_key}&base=USD&symbols=XAU"
    data = fetch_json(url)
    if not data.get("success"):
        raise RuntimeError(f"metals-api 오류: {data}")
    return float(data["rates"]["XAU"])


def fetch_usd_krw():
    url = "https://api.frankfurter.app/latest?from=USD&to=KRW"
    data = fetch_json(url)
    return float(data["rates"]["KRW"])


def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def main():
    gold_usd_oz = fetch_gold_usd_per_oz()
    usd_krw = fetch_usd_krw()
    krw_per_gram = (gold_usd_oz / OZ_TO_GRAM) * usd_krw

    today = datetime.date.today().isoformat()
    history = load_history()
    history = [h for h in history if h["date"] != today]
    history.append({
        "date": today,
        "goldUsdOz": round(gold_usd_oz, 2),
        "usdKrw": round(usd_krw, 2),
        "krwPerGram": round(krw_per_gram, 1),
    })
    history.sort(key=lambda h: h["date"])
    history = history[-KEEP_DAYS:]
    save_history(history)
    print(f"저장 완료: {today} | {gold_usd_oz} USD/oz | {usd_krw} USD/KRW | {round(krw_per_gram,1)} 원/g")


if __name__ == "__main__":
    main()
