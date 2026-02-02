import scrape
import clean


def main(url):
    results = scrape.scrape_data(url)
   # clean.clean_data(results)


if __name__ == "__main__":
    base_url = "https://www.thegradcafe.com/"
    main(base_url)