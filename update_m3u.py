import os
import re
import time
import cloudscraper
import base64

PLAYLIST_FILE = "playlist.m3u"
BUFFER_TIME = 1800 

def fetch_fresh_link(ch_id):
    """Cloudscraper ব্যবহার করে সার্ভার ব্লক বাইপাস করে আসল টোকেন আনার ফাংশন"""
    url = f"https://donis.jimpenopisonline.online/premiumtv/daddy3.php?id={ch_id}"
    
    headers = {
        "referer": "https://dlhd.pk/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # সাধারণ requests এর বদলে cloudscraper ব্যবহার
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    try:
        response = scraper.get(url, headers=headers, timeout=15)
        match = re.search(r"window\.atob\(['\"]([^'\"]+)['\"]\)", response.text)
        
        if match:
            base64_string = match.group(1)
            fresh_m3u8_link = base64.b64decode(base64_string).decode('utf-8')
            return fresh_m3u8_link
        else:
            print(f"[-] Token not found for ID {ch_id}. Server response blocked.")
            return None
            
    except Exception as e:
        print(f"[-] Error fetching ID {ch_id}: {e}")
        return None

def monitor_and_update_playlist():
    if not os.path.exists(PLAYLIST_FILE):
        print("[-] Playlist file not found!")
        return

    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_time = int(time.time())
    updated_lines = []
    has_changes = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF"):
            extinf_line = line
            url_line = lines[i+1].strip() if i+1 < len(lines) else ""
            
            ch_id_match = re.search(r'tvg-id="([^"]+)"', extinf_line)
            expires_match = re.search(r'expires=(\d+)', url_line)
            
            if ch_id_match and expires_match:
                ch_id = ch_id_match.group(1)
                expires_time = int(expires_match.group(1))
                time_left = expires_time - current_time
                
                if time_left < BUFFER_TIME:
                    print(f"[*] Updating ID: {ch_id}...")
                    new_link = fetch_fresh_link(ch_id)
                    
                    if new_link:
                        url_line = new_link
                        has_changes = True
                        print(f"[+] Success! Got original link for ID: {ch_id}")
                    else:
                        print(f"[-] Failed. Keeping old link for ID: {ch_id}")
            
            updated_lines.append(extinf_line + "\n")
            updated_lines.append(url_line + "\n")
            i += 2 
            
        else:
            if line: 
                updated_lines.append(line + "\n")
            i += 1

    if has_changes:
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        print("\n[+] Playlist successfully updated with ORIGINAL links!")

if __name__ == "__main__":
    monitor_and_update_playlist()
