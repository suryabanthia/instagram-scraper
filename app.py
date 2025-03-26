from flask import Flask, jsonify, request
import requests
import time
import json

app = Flask(__name__)

def get_user_id(username):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["graphql"]["user"]["id"]
    return None

def scrape_followers(username, sessionid, max_followers=500):
    user_id = get_user_id(username)
    if not user_id:
        return {"error": f"Could not find user ID for {username}"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-IG-App-ID": "936619743392459"
    }
    cookies = {
        "sessionid": sessionid
    }

    followers = []
    after = None
    while len(followers) < max_followers:
        url = f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count=50"
        if after:
            url += f"&after={after}"

        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code != 200:
            return {"error": f"Failed to fetch followers: {response.status_code} - {response.text}"}

        data = response.json()
        users = data.get("users", [])
        for user in users:
            username = user.get("username")
            if username and username not in followers:
                followers.append(username)
                if len(followers) >= max_followers:
                    break

        after = data.get("next_max_id")
        if not after:
            break

        time.sleep(1)

    return {"followers": followers}

@app.route("/scrape_followers", methods=["GET"])
def scrape_followers_endpoint():
    username = request.args.get("username")
    sessionid = request.args.get("sessionid")
    max_followers = int(request.args.get("max_followers", 500))

    if not username or not sessionid:
        return jsonify({"error": "Username and sessionid are required"}), 400

    result = scrape_followers(username, sessionid, max_followers)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)