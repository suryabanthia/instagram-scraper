from flask import Flask, jsonify, request
import requests
import logging
from collections import OrderedDict
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "Server is running"})

@app.route('/test')
def test():
    return jsonify({"message": "Test endpoint is working"})

@app.route('/scrape_followers')
def scrape_followers():
    try:
        user_id = request.args.get('user_id')
        sessionid = request.args.get('sessionid')
        after = request.args.get('after')  # Get the after parameter for pagination
        
        if not user_id or not sessionid:
            return jsonify({"error": "Missing required parameters"}), 400
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "X-IG-App-ID": "936619743392459",
            "X-IG-Device-ID": "android-2b3f8d9c",
            "X-IG-Android-ID": "android-2b3f8d9c",
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Capabilities": "3brTvw==",
            "X-IG-Device-Locale": "en_US",
            "X-IG-App-Locale": "en_US",
            "X-IG-Timezone-Offset": "3600",
            "X-IG-Device-Id": "android-2b3f8d9c",
            "X-IG-Android-ID": "android-2b3f8d9c",
            "X-IG-WWW-Claim": "0",
            "X-IG-Request-Signature": "missing",
            "X-IG-Device-Id": "android-2b3f8d9c",
            "X-IG-Android-ID": "android-2b3f8d9c",
            "X-IG-Device-Locale": "en_US",
            "X-IG-App-Locale": "en_US",
            "X-IG-Timezone-Offset": "3600",
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Capabilities": "3brTvw==",
            "X-IG-Device-Id": "android-2b3f8d9c",
            "X-IG-Android-ID": "android-2b3f8d9c",
            "X-IG-Device-Locale": "en_US",
            "X-IG-App-Locale": "en_US",
            "X-IG-Timezone-Offset": "3600",
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Capabilities": "3brTvw=="
        }
        cookies = {
            "sessionid": sessionid,
            "csrftoken": "missing",
            "mid": "missing",
            "ds_user_id": user_id
        }
        
        # Use GraphQL endpoint for better pagination
        variables = {
            "id": user_id,
            "first": 100,
            "after": after
        }
        
        # Use a different query hash that's known to work
        url = "https://www.instagram.com/graphql/query/?query_hash=5aefa9893005572d237da5068082d8d5&variables=" + json.dumps(variables)
            
        logger.debug(f"Making request to URL: {url}")
        response = requests.get(url, headers=headers, cookies=cookies)
        
        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch followers: {response.status_code}"}), response.status_code
            
        data = response.json()
        logger.debug(f"Response data: {data}")  # Add debug logging for response
        
        edges = data.get("data", {}).get("user", {}).get("edge_followed_by", {}).get("edges", [])
        
        # Extract followers from edges
        followers = []
        for edge in edges:
            node = edge.get("node", {})
            if node:
                followers.append(node.get("username"))
        
        # Get pagination info
        page_info = data.get("data", {}).get("user", {}).get("edge_followed_by", {}).get("page_info", {})
        has_next_page = page_info.get("has_next_page", False)
        end_cursor = page_info.get("end_cursor")
        
        return jsonify({
            "followers": followers,
            "next_page_token": end_cursor,
            "total_count": data.get("data", {}).get("user", {}).get("edge_followed_by", {}).get("count", 0),
            "current_count": len(followers),
            "has_more": has_next_page,
            "page_size": 100
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/scrape_all_followers')
def scrape_all_followers():
    try:
        user_id = request.args.get('user_id')
        sessionid = request.args.get('sessionid')
        
        if not user_id or not sessionid:
            return jsonify({"error": "Missing required parameters"}), 400
            
        # Use OrderedDict to maintain order while removing duplicates
        all_followers = OrderedDict()
        next_page_token = None
        page = 1
        
        while True:
            # Construct URL with pagination
            url = f"http://127.0.0.1:5000/scrape_followers?user_id={user_id}&sessionid={sessionid}"
            if next_page_token:
                url += f"&after={next_page_token}"
                
            response = requests.get(url)
            data = response.json()
            
            if "error" in data:
                return jsonify({"error": data["error"]}), 500
                
            followers = data.get("followers", [])
            for follower in followers:
                all_followers[follower] = True
            
            # Check if we have more pages
            if not data.get("has_more"):
                break
                
            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break
                
            page += 1
            logger.debug(f"Fetched page {page}, total unique followers so far: {len(all_followers)}")
            
        return jsonify({
            "total_followers": len(all_followers),
            "followers": list(all_followers.keys()),
            "pages_fetched": page
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting server...")
    print("Available routes:")
    print("  - /")
    print("  - /test")
    print("  - /scrape_followers (100 followers per page)")
    print("  - /scrape_all_followers (fetches all followers)")
    app.run(debug=True, port=5000)
