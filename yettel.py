import requests
from bs4 import BeautifulSoup
import logging
import os

### Konfiguracija
URLS_FILE = "./urls.txt"
WEBHOOK_URL = os.environ.get('yettel_webhook')

### Loggin leveli
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_urls_from_file(file_path):
    """Read URLs from a file and return them as a list."""
    ### Čitanje prethodno obrađenih URL-ova iz fajla (Urađeno kako bi se koliko toliko čuvalo stanje)
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file.readlines()]
    return urls

def check_for_zakon(url):
    ### Provera da li se reč 'Zakon' javlja u text-u (Za sada primećeno da se taj reč navodi kada je promena cene u pitanju)
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        if 'Zakon' in soup.get_text():
            return True
    except requests.RequestException as e:
        logger.error(f"Failed to retrieve {url}: {e}")
    return False

def notify_discord(url):
    ### Slanje notifikacija na Discord kanale
    json_data = {'content': "Moguća je promena cena paketa, molim proverite link: " + url}
    response = requests.post(WEBHOOK_URL, json=json_data)
    
    ### https://discord.com/developers/docs/resources/webhook#execute-webhook 
    if response.status_code != 204:
        logger.error(f"Failed to notify Discord about {url}. Status code: {response.status_code}")

def main():
    ### Slanje GET poziva kako bi se dobili URL-ovi svih Yettel vesti (trenutno je po godinama, i 2024. je Default)
    url = "https://www.yettel.rs/sr/privatni/podrska/obavestenja-za-korisnike/"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to retrieve {url}: {e}")
        return

    ### Učitavanje trenutnih URL-ova iz fajla
    urls = read_urls_from_file(URLS_FILE)
    
    ### Lista u kojoj će se dodati svi novi skrejpovani URL-ovi, koji će kasnije biti dodati u urls.txt fajl
    final_list = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        div_posts_wrapper = soup.find('div', class_='posts-wrapper')
        if div_posts_wrapper:
            a_elements = div_posts_wrapper.find_all('a')
            unique_href_links = set()
            for a in a_elements:
                href = a.get('href')
                if href:
                    unique_href_links.add(href)
            for href in unique_href_links:
                if href not in urls:
                    if check_for_zakon(href):
                        logger.info(f"Word 'Zakon' found in: {href}")
                        final_list.append(href)
                        notify_discord(href)
                    else:
                        logger.info(f"Word 'Zakon' not found in: {href}")
                        final_list.append(href)
                else:
                    logger.info(f"URL already processed: {href}")
        else:
            logger.warning("No <div> element with class 'posts-wrapper' found.")
    else:
        logger.error(f"Failed to retrieve the webpage. Status code: {response.status_code}")

    ### Dodvanje svih novih skrepovanih URL-ova u fajl
    with open(URLS_FILE, 'a') as file:
        for url in final_list:
            file.write(url + "\n")

if __name__ == "__main__":
    main()
