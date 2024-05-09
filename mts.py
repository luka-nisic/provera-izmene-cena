import requests
from bs4 import BeautifulSoup
import logging
import os

### Konfiguracija
URLS_FILE = "./urls.txt"
WEBHOOK_URL = os.environ.get('mts_webhook')

### Logging leveling
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def notify_discord(url):
    ### Slanje notifikacija na Discord kanale
    json_data = {'content': "Moguća je promena cena paketa, molim proverite link: " + url}
    response = requests.post(WEBHOOK_URL, json=json_data)
    
    ### https://discord.com/developers/docs/resources/webhook#execute-webhook 
    if response.status_code != 204:
        logger.error(f"Failed to notify Discord about {url}. Status code: {response.status_code}")


def extract_content(url):
    ### Provera da li se reč 'Zakon' javlja u text-u (Za sada primećeno da se taj reč navodi kada je promena cene u pitanju)
    try:
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content_elements = soup.select('main#page-wrap div.acl-holder div.container div.row div.bootstrap-col-md-8.col-md-8 div.container section.single-news div.story-page-content.full-width-left.js-story-page-content.content p')
            content = "\n".join([element.get_text() for element in content_elements])
            if "Zakon" in content:
                logger.info(f"Word 'Zakon' found in: {url}")
                notify_discord(url)
            else:
                logger.info(f"Content on {url} does not mention 'Zakon'.")
            return content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch content from {url}: {e}")
    return None

def read_urls_from_file(file_path):
    ### Čitanje prethodno obrađenih URL-ova iz fajla (Urađeno kako bi se koliko toliko čuvalo stanje)
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file.readlines()]
    return urls

def main():
    ### Učitavanje URL-ova iz fajla
    urls = read_urls_from_file(URLS_FILE)

    ### Ovi URL-ovi se koriste kako bismo dobili zandnjih xyz vesti sa MTS-ovog sajta (nepoznato mi je da li mogu sve vesti da uzmem odjednom)
    main_urls = [
        "https://mts.rs/content/big9small/1/1/1",
        "https://mts.rs/content/big9small/1/1/2"
    ]

    ### Neophodni hederi
    headers = {
        "Connection": "keep-alive",
        "Referer": "https://mts.rs/Privatni/Korisnicka-zona/Vesti/Servisne-informacije"
    }

    ### Lista u kojoj će se dodati svi novi skrejpovani URL-ovi, koji će kasnije biti dodati u urls.txt fajl
    final_list = []

    for main_url in main_urls:
        logger.info(f"Processing main URL: {main_url}")
        try:
            response = requests.get(main_url, headers=headers)
            response.raise_for_status()
            main_html_content = response.text
            main_soup = BeautifulSoup(main_html_content, 'html.parser')
            links = main_soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                full_url = href
                if full_url not in urls:
                    logger.info(f"Extracting content from: {full_url}")
                    content = extract_content(full_url)
                    if content:
                        final_list.append(full_url)
                else:
                    logger.info(f"URL already processed: {full_url}")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch content from main URL {main_url}: {e}")

    ### Dodvanje svih novih skrepovanih URL-ova u fajl
    with open(URLS_FILE, 'a') as file:
        for url in final_list:
            file.write(url + "\n")

if __name__ == "__main__":
    main()
