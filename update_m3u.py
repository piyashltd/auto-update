import os
import re
import time
import requests
import base64
import urllib3

# SSL ওয়ার্নিং বন্ধ করার জন্য
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PLAYLIST_FILE = "playlist.m3u"
# মেয়াদ শেষ হওয়ার কতক্ষণ আগে লিংক আপডেট হবে (সেকেন্ডে)। 1800 সেকেন্ড = 30 মিনিট
BUFFER_TIME = 1800 

def fetch_fresh_link(ch_id):
    """সার্ভার থেকে নতুন টোকেন আনার ফাংশন (ডিবাগ মোডসহ)"""
    url = f"https://donis.jimpenopisonline.online/premiumtv/daddy3.php?id={ch_id}"
    
    headers = {
        "authority": "donis.jimpenopisonline.online",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-BD,en;q=0.9,ar-BD;q=0.8,ar;q=0.7,en-GB;q=0.6,en-US;q=0.5",
        "referer": "https://dlhd.pk/",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "upgrade-insecure-requests": "1",
        "sec-fetch-dest": "iframe",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        print(f"\n[*] ID {ch_id} এর জন্য সার্ভারের স্ট্যাটাস কোড: {response.status_code}")
        
        match = re.search(r"window\.atob\(['\"]([^'\"]+)['\"]\)", response.text)
        
        if match:
            base64_string = match.group(1)
            fresh_m3u8_link = base64.b64decode(base64_string).decode('utf-8')
            return fresh_m3u8_link
        else:
            print(f"[-] টোকেন পাওয়া যায়নি! সার্ভার থেকে যা এসেছে (প্রথম ৫০০ অক্ষর):\n{response.text[:500]}\n")
            return None
            
    except Exception as e:
        print(f"[-] Error fetching ID {ch_id}: {e}")
        return None

def monitor_and_update_playlist():
    if not os.path.exists(PLAYLIST_FILE):
        print("[-] Playlist file not found! Please create a basic playlist.m3u first.")
        return

    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_time = int(time.time())
    updated_lines = []
    has_changes = False

    i = 0
    print("[*] Checking playlist tokens...")
    
    while i < len(lines):
        line = lines[i].strip()
        
        # যদি লাইনটি চ্যানেলের মেটাডেটা হয়
        if line.startswith("#EXTINF"):
            extinf_line = line
            url_line = lines[i+1].strip() if i+1 < len(lines) else ""
            
            # tvg-id এবং expires টোকেন বের করা
            ch_id_match = re.search(r'tvg-id="([^"]+)"', extinf_line)
            expires_match = re.search(r'expires=(\d+)', url_line)
            
            if ch_id_match and expires_match:
                ch_id = ch_id_match.group(1)
                expires_time = int(expires_match.group(1))
                time_left = expires_time - current_time
                
                # যদি মেয়াদ শেষ হতে ৩০ মিনিটের কম সময় বাকি থাকে
                if time_left < BUFFER_TIME:
                    print(f"[*] Token expiring soon for ID: {ch_id} (Time left: {time_left//60} mins). Updating...")
                    new_link = fetch_fresh_link(ch_id)
                    
                    if new_link:
                        url_line = new_link # অরিজিনাল টোকেনযুক্ত লিংকটি এখানে বসে যাবে
                        has_changes = True
                        print(f"[+] Successfully updated ID: {ch_id}")
                    else:
                        print(f"[-] Failed to update ID: {ch_id}, keeping old link.")
                else:
                    print(f"[+] Token valid for ID: {ch_id} (Time left: {time_left//60} mins). Skipping.")
            
            # মেটাডেটা এবং লিংক ফাইলে যোগ করা
            updated_lines.append(extinf_line + "\n")
            updated_lines.append(url_line + "\n")
            i += 2 
            
        else:
            if line: 
                updated_lines.append(line + "\n")
            i += 1

    # পরিবর্তন আসলে সেভ করা
    if has_changes:
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        print("\n[+] Playlist updated and saved successfully!")
    else:
        print("\n[*] No tokens needed updating. Playlist is up to date.")

if __name__ == "__main__":
    monitor_and_update_playlist()
