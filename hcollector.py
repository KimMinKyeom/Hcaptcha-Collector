import requests
import os
import string
import random
import asyncio
import json
import time
import jwt
import nest_asyncio
from python_ghost_cursor import path
from pyppeteer import launch

class HcaptchaCollector:
    def __init__(self, s, repetition):
        nest_asyncio.apply()
        self.s = s
        self.repetition = repetition
        self.headers = {
            'Authority': "hcaptcha.com",
            'Accept': "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            'Origin': "https://newassets.hcaptcha.com",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.70 Whale/3.13.131.27 Safari/537.36'
        }
    def _request(self, method, url, type_="", payload={}, headers={}, proxy=True):
        session = self.s if proxy else requests.session()
        for attempt in range(4):  # Retry up to 4 times
            try:
                if type_ == 'data':
                    response = session.request(method, url, data=payload, headers=headers)
                elif type_ == 'json':
                    response = session.request(method, url, json=payload, headers=headers)
                else:
                    response = session.request(method, url, headers=headers)
                return response
            except Exception as e:
                print(f"Request error: {e}, retrying... (Attempt {attempt + 1}/4)")
                continue
        return None

    async def _get_hsw(self, resp):
        try:
            # Decode the JWT token without verification
            decoded = jwt.decode(resp, options={"verify_signature": False})
            url = decoded.get('l', '')
            version = url.split("https://newassets.hcaptcha.com/c/")[1]
            hsw_response = self._request('get', url + "/hsw.js")
            if hsw_response is None:
                print("Failed to retrieve hsw.js content.")
                return None, version
            hsw = hsw_response.text

            # Use a local Chromium installation path
            chromium_path = r'C:\Users\skibidi\Desktop\hcaptchasolver\chrome-win\chrome.exe' #Replace with your own chromium path!
            browser = await launch({
                "headless": True,
                "executablePath": chromium_path
            }, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False)
            page = await browser.newPage()
            await page.addScriptTag({'content': hsw})
            result = await page.evaluate(f'hsw("{resp}")')
            await browser.close()
            return result, version
        except Exception as e:
            print(f"Error in _get_hsw: {e}")
            return None, None

    def collect(self, site_key, host):
        start = {'x': 100, 'y': 100}
        end = {'x': 600, 'y': 700}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for _ in range(self.repetition):
            try:
                timestamp = int(time.time() * 1000) + round(random.random() * (120 - 30) + 30)

                resp = self._request('get', f'https://hcaptcha.com/checksiteconfig?host={host}&sitekey={site_key}&sc=1&swa=1', headers=self.headers)
                if resp is None or resp.status_code != 200:
                    print(f"Failed to get site config: {resp}")
                    continue

                motion_path = path(start, end)
                mm = [[int(p['x']), int(p['y']), int(time.time() * 1000) + round(random.random() * (5000 - 2000) + 2000)] for p in motion_path]

                hsw, version = loop.run_until_complete(self._get_hsw(resp.json().get('c', {}).get('req')))
                if not hsw:
                    print("Failed to get hsw or version.")
                    continue

                payload = {
                    'sitekey': site_key,
                    'host': host,
                    'hl': 'ko',
                    'motionData': json.dumps({'st': timestamp, 'dct': timestamp, 'mm': mm}),
                    'n': hsw,
                    'v': version,
                    'c': json.dumps(resp.json()['c'])
                }

                get_task = self._request('post', f"https://hcaptcha.com/getcaptcha?s={site_key}", "data", payload=payload, headers=self.headers)
                if get_task is None or get_task.status_code != 200:
                    print(f"Failed to get captcha: {get_task}")
                    continue

                task_list = get_task.json().get('tasklist', [])

                files = [img for img in os.listdir('./imgs')]

                for img in task_list:
                    filename = None
                    while not filename or filename + ".png" in files:
                        filename = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 10)))

                    img_response = self._request('get', img['datapoint_uri'], proxy=False)
                    if img_response and img_response.status_code == 200:
                        with open(f'./imgs/{filename}.png', 'wb') as f:
                            f.write(img_response.content)
                            print(f"Saved image as {filename}.png")
                    else:
                        print(f"Failed to download image from {img['datapoint_uri']}")

            except Exception as e:
                print(f"Error during collection: {e}")

if __name__ == "__main__":
    if not os.path.exists('./imgs'):
        os.makedirs('./imgs')

    session = requests.session()
    # session.proxies.update({"http": "proxy", 'https': "proxy"}) # Uncomment to use proxies
    collector = HcaptchaCollector(session, 1)
    collector.collect("site key", "url")  # Ex. '4c672d35-0701-42b2-88c3-78380b0db560', 'discord.com'