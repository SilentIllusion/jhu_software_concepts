import urllib3
import scrape

def main():
    base_url = "https://www.thegradcafe.com/"
    paths = [
        "/",
        "/survey"
    ]
    agent = 'donna'

    perms = scrape.permission(base_url, paths, agent)
    for path, allowed in perms.items():
        if allowed:
            scrape.scrape_data(base_url)
        else: 
            print(f"Blocked by robots.txt: {path}")



if __name__ == "__main__":
    main()