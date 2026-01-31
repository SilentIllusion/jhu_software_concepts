from bs4 import BeautifulSoup
import urllib3
import json

http = urllib3.PoolManager()
url = "https://www.thegradcafe.com/survey/"

response = http.request('GET', url)
print(response.status)

html = response.read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')
text = soup.get_text()
print(text)
spaceless_text = text.replace('\n\n', '')


print(spaceless_text)