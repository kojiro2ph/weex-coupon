import requests
import json
import csv
import time

API_KEY = "pk_RSR9XB_eceb372eda1ed6b818468e4febaeb324af"
REVISION = "2026-04-15"

BASE_URL = "https://a.klaviyo.com/api"

headers = {
    "Authorization": f"Klaviyo-API-Key {API_KEY}",
    "accept": "application/json",
    "revision": REVISION
}


# ----------------------------
# Event 一覧取得
# ----------------------------
def get_events():

    url = f"{BASE_URL}/events/"

    params = {
        "page[size]": 100
    }

    events = []

    while url:

        print(f"Fetching events: {url}")

        response = requests.get(
            url,
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            print("ERROR EVENTS:", response.status_code)
            print(response.text)
            break

        data = response.json()

        events.extend(data.get("data", []))

        next_link = data.get("links", {}).get("next")

        if next_link:
            url = next_link
            params = None
        else:
            url = None

        time.sleep(0.2)

    return events


# ----------------------------
# Profile 取得
# ----------------------------
def get_profile(profile_id):

    if not profile_id:
        return None

    url = f"{BASE_URL}/profiles/{profile_id}"

    response = requests.get(
        url,
        headers=headers
    )

    if response.status_code != 200:
        print(f"PROFILE ERROR: {profile_id}")
        return None

    data = response.json()

    attributes = data.get("data", {}).get("attributes", {})

    return {
        "email": attributes.get("email"),
        "first_name": attributes.get("first_name"),
        "last_name": attributes.get("last_name")
    }


# ----------------------------
# Coupon Event 抽出
# ----------------------------
def extract_coupon_events(events):

    results = []

    for event in events:

        attributes = event.get("attributes", {})
        properties = attributes.get("event_properties", {})

        metric = attributes.get("metric", {})
        event_name = metric.get("name", "")

        # coupon 関連だけ
        text_blob = json.dumps(properties).lower()

        if (
            "coupon" not in event_name.lower()
            and "coupon" not in text_blob
            and "discount" not in text_blob
        ):
            continue

        profile_data = (
            event.get("relationships", {})
            .get("profile", {})
            .get("data", {})
        )

        profile_id = profile_data.get("id")

        # Profile API から email 取得
        profile = get_profile(profile_id)

        result = {
            "event_name": event_name,
            "timestamp": attributes.get("datetime"),
            "profile_id": profile_id,
            "email": profile.get("email") if profile else None,
            "first_name": profile.get("first_name") if profile else None,
            "last_name": profile.get("last_name") if profile else None,

            "coupon_code": (
                properties.get("coupon_code")
                or properties.get("coupon")
                or properties.get("code")
                or properties.get("discount_code")
            ),

            "coupon_name": (
                properties.get("coupon_name")
                or properties.get("coupon_title")
                or properties.get("discount_name")
            ),

            "raw_properties": properties
        }

        results.append(result)

        print(
            f"[FOUND] {result['email']} "
            f"=> {result['coupon_code']}"
        )

        time.sleep(0.2)

    return results


# ----------------------------
# CSV 保存
# ----------------------------
def save_csv(rows, filename="coupon_report.csv"):

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:

        writer = csv.writer(f)

        writer.writerow([
            "email",
            "first_name",
            "last_name",
            "coupon_code",
            "coupon_name",
            "event_name",
            "timestamp",
            "profile_id"
        ])

        for row in rows:

            writer.writerow([
                row["email"],
                row["first_name"],
                row["last_name"],
                row["coupon_code"],
                row["coupon_name"],
                row["event_name"],
                row["timestamp"],
                row["profile_id"]
            ])

    print(f"CSV saved: {filename}")


# ----------------------------
# Main
# ----------------------------
def main():

    events = get_events()

    print(f"TOTAL EVENTS: {len(events)}")

    coupon_events = extract_coupon_events(events)

    print(f"COUPON EVENTS: {len(coupon_events)}")

    # JSON保存
    with open(
        "coupon_events.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            coupon_events,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("JSON saved")

    # CSV保存
    save_csv(coupon_events)


if __name__ == "__main__":
    main()