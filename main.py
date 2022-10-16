import logging
from selenium.webdriver.support import expected_conditions as EC
import requests
import undetected_chromedriver as uc
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
import os
import ipaddress
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputFile
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException

os.environ['WDM_SSL_VERIFY'] = '0'
WORKING = False

def SearchByIp(target):
    infos=[]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'TE': 'trailers',
    }
    i=0
    response = requests.get(f'''https://search.censys.io/hosts/{target}''', headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    results = soup.find(id="content")
    ports = results.find_all("div", class_="protocol-details")
    for port in ports:
        soup = BeautifulSoup(str(port), features="lxml")
        results = soup.h2
        results = str(results.text)
        results = results.replace(" ", "")
        results = results.split('\n')
        results = results[1].split("/")
        infos.append((results[0], results[1]))
    return(infos)

API_TOKEN = '5405623026:AAFI4YRUunST0DopqL7xmRF0HXLNzHHakHA'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def create_screen(ip, port, s):
    try:
        os.remove("screenshot.png")
    except OSError:
        pass
    try:
        options = Options()
        options.headless = True
        options.add_argument('--headless')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--safebrowsing-disable-extension-blacklist")
        options.add_argument("--safebrowsing-disable-download-protection")
        options.add_argument('--enable-javascript')
        options.add_argument("--no-sandbox")
        desired_capabilities = DesiredCapabilities.CHROME.copy()
        desired_capabilities['acceptInsecureCerts'] = True
        driver = uc.Chrome(chrome_options=options, options=options, desired_capabilities=desired_capabilities)

        print(f'http{s}://{ip}:{port}')
        driver.get(f'http{s}://{ip}:{port}')
        try:
            WebDriverWait(driver, 1).until(EC.alert_is_present(),
                                            'Timed out waiting for PA creation ' +
                                            'confirmation popup to appear.')

            alert = driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            pass
        WebDriverWait(driver, 5).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

        driver.set_window_size(800, 600)
        driver.get_screenshot_as_file("screenshot.png")
        driver.quit()
        return InputFile("screenshot.png")
    except Exception as ex:
        return str(ex)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["/scan_pool all"]
    keyboard.add(*buttons)
    await message.answer("Usage: /scan_pool <address pool> \n Ex: /scan_pool 196.168.0.0/16\n To scan all yandex: /scan_pool all", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Какая там команада?")
async def with_puree(message: types.Message):
    await message.answer("Ex: /scan_pool 196.168.0.0/16")

all = [
"51.250.0.0/17",
"62.84.112.0/20",
"84.201.128.0/18",
"84.252.128.0/20",
"89.169.128.0/18",
"130.193.32.0/19",
"158.160.0.0/16",
"178.154.192.0/18",
"178.170.222.0/24",
"185.206.164.0/22",
"193.32.216.0/22",
"217.28.224.0/20"]

@dp.message_handler(commands=['scan_pool'])
async def echo(message: types.Message):
    global WORKING
    await message.answer(f"Fuck you")
    if WORKING:
        await message.answer(f"Fuck off bitches.")
        return 0
    WORKING = True
    try:
        req = message.text.split()
        ips = [req[1]]
        if ips[0] == "all":
            ips = all
        for i in ips:
            rrr = []
            if i == "51.250.0.0/17":
                rrr = list(ipaddress.IPv4Network(i, strict=False))[1001:]
            else:
                rrr = ipaddress.IPv4Network(i, strict=False)
            for ip in rrr:
                print(ip)
                info = list(set(SearchByIp(ip)))
                print(info)
                s = ""
                if info:
                    for port in info:
                        if port[1] == "HTTP":
                            try:
                                res = requests.get(f'https://{ip}:{port[0]}', verify=False, timeout=10)
                                s = "s"
                            except requests.exceptions.RequestException as e:
                                try:
                                    res = requests.get(f'http://{ip}:{port[0]}', timeout=10)
                                    s = ""
                                except:
                                    continue
                            res = res.status_code
                            if res // 100 != 5 and res // 100 != 4:
                                await message.answer(f"Find port {ip}:{port[0]}")
                                screen = create_screen(ip, port[0], s)
                                if type(screen) is str:
                                    await message.answer("ERROR:")
                                    await message.answer(screen)
                                else:
                                    await bot.send_photo(chat_id=message.chat.id, photo=screen)
                                    sleep(1.5)
        await message.answer(f"END SCANNING")
        WORKING = False
    except Exception as ex:
        await message.answer("ERROR:")
        await message.answer(ex)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


# 51.250.1.157
# [('80', 'HTTP'), ('5432', 'POSTGRES'), ('22', 'SSH'), ('443', 'HTTP')]