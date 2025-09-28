import requests
import json

BASE_URL = "https://fbrapi.com"

def get_api_key():
    r = requests.post(f"{BASE_URL}/generate_api_key")
    r.raise_for_status()
    return r.json()["api_key"]

def pretty_print_response(name, response, max_rows=5):
    print(f"\n➡️ {name} | Status: {response.status_code}")
    try:
        data = response.json()
        if "data" in data and isinstance(data["data"], list):
            rows = data["data"]
            print(f"{len(rows)} rows total")
            for row in rows[:max_rows]:
                print(json.dumps(row, indent=2)[:1000])
        else:
            # Print whole JSON if no "data" list
            print(json.dumps(data, indent=2)[:2000])
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
        print(response.text[:1000])

if __name__ == "__main__":
    # Get API key
    API_KEY = get_api_key()
    HEADERS = {"X-API-Key": API_KEY}
    print("✅ API key generated")

    LEAGUE_ID = 9   # Premier League
    SEASON = 2019   # Example season

    # League-Seasons
    # r1 = requests.get(f"{BASE_URL}/league-seasons", headers=HEADERS, params={"league_id": LEAGUE_ID})
    # pretty_print_response("League-Seasons", r1)

    # # Teams
    # r2 = requests.get(f"{BASE_URL}/teams", headers=HEADERS, params={"league_id": LEAGUE_ID, "season": SEASON})
    # pretty_print_response("Teams", r2)
    # resp = requests.get(
    # "https://fbrapi.com/teams",
    # headers=HEADERS,
    # params={"league_id": 9, "season": 2019}
    # )
    # print("Status Code:", resp.status_code)

    # try:
    #     data = resp.json()
    #     print("Raw JSON:")
    #     print(json.dumps(data, indent=2))   # pretty print the entire JSON
    # except Exception as e:
    #     print("❌ Failed to parse JSON:", e)
    #     print(resp.text[:1000])  # fallback: print raw text

resp = requests.get("https://fbrapi.com/league-seasons", headers=HEADERS, params={"league_id": 9})
print(json.dumps(resp.json(), indent=2))
