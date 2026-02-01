from bs4 import BeautifulSoup
import urllib3
import re

def scrape_data(url):
    http = urllib3.PoolManager()
    path = "survey/index.php"

    response = http.request("GET", url + path)

    print("Status:", response.status)

    if response.status == 200:
        soup = BeautifulSoup(response.data, "html.parser")

        schools = soup.select("td.instcol")

        print("Schools found:", len(schools))

        for school in schools[:10]:
            print(school.get_text(strip=True))
    else:
        print("Request failed")

########
def permission(url, paths, agent):
    path = "robots.txt"

    http = urllib3.PoolManager()

    if not url.endswith("/"):
        url += "/"
    
    request = http.request("GET", url + path)
    
    if request.status == 200:
        text = (request.data or b"").decode("utf-8", errors="replace")
        #print(text)
    
    # --------------------------------------------------
    # Parse robots.txt
    # --------------------------------------------------
    disallow = []
    active = False

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        m = re.match(r"^\s*([A-Za-z\-]+)\s*:\s*(.*?)\s*$", line)
        if not m:
            continue

        key = m.group(1).lower()
        val = m.group(2).strip()

        if key == "user-agent":
            ua = val.lower()
            active = (ua == agent.lower() or ua == "*")
            continue

        if active and key == "disallow":
            disallow.append(val)

    # Check each path
    perms = {}

    for path in paths:
        allowed = True
        for rule in disallow:
            if rule and path.startswith(rule):
                allowed = False
                break
        perms[path] = allowed

    return perms
    





