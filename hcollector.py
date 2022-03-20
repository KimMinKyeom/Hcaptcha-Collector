import requests, os, string, random, asyncio, json, time, jwt, nest_asyncio
from pyppeteer_ghost_cursor import path
from pyppeteer import launch


class HcaptchaCollector:
    def __init__(self, s, repetition):
        nest_asyncio.apply()
        self.s = s
        self.repetition = repetition
        self.headers = {'Authority': "hcaptcha.com", 'Accept': "application/json", "Accept-Language": "en-US,en;q=0.9", "Content-Type": "application/x-www-form-urlencoded", 'Origin': "https://newassets.hcaptcha.com", "Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.70 Whale/3.13.131.27 Safari/537.36'}

    def _request(self, method, url, type_="", payload={}, headers={}, proxy=True):
        if not proxy:
            s = requests.session()
        else:
            s = self.s
        count = 0
        while count <= 3:
            try:
                if type_ == 'data':
                    return s.request(method, url, data=payload, headers=headers)
                elif type_ == 'json':
                    return s.request(method, url, json=payload, headers=headers)
                else:
                    return s.request(method, url, headers=headers)
            except:
                count += 1
        else:
            return False

    async def _get_hsw(self, resp):
        url = jwt.decode(resp, options={"verify_signature": False})['l']
        version = url.split("https://newassets.hcaptcha.com/c/")[1]
        hsw = self._request('get', url + "/hsw.js").text
        count = 0
        while count <= 3:
            try:
                browser = await launch({"headless": True}, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False)
                page = await browser.newPage()
                await page.addScriptTag({'content': hsw})
                resp = await page.evaluate(f'hsw("{resp}")')
                await browser.close()
                return resp, version
            except:
                try:
                    await browser.close()
                except:
                    pass
                count += 1

    def collect(self, site_key, host):
        start = {'x': 100, 'y': 100}
        end = {'x': 600, 'y': 700}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for _ in range(self.repetition):
            try:
                timestamp = int((time.time() * 1000) + round(random.random() * (120 - 30) + 30))
                resp = self._request('get', f'https://hcaptcha.com/checksiteconfig?host={host}&sitekey={site_key}&sc=1&swa=1', headers=self.headers)
                if resp.status_code != 200:
                    continue

                mm = [[int(p['x']), int(p['y']), int(time.time() * 1000) + round(random.random() * (5000 - 2000) + 2000)] for p in path(start, end)]
                hsw, version = loop.run_until_complete(self._get_hsw(resp.json()['c']['req']))

                payload = {'sitekey': site_key, 'host': host, 'hl': 'ko', 'motionData': json.dumps({'st': timestamp, 'dct': timestamp, 'mm': mm}), 'n': hsw, 'v': version, 'c': json.dumps(resp.json()['c'])}
                get_task = self._request('post', f"https://hcaptcha.com/getcaptcha?s={site_key}", "data", payload=payload, headers=self.headers)
                if get_task.status_code != 200:
                    continue
                get_task = get_task.json()
                files = [img for img in os.listdir(f'./imgs')]
                for img in get_task['tasklist']:
                    while True:
                        filename = "".join([random.choice(string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 10))])
                        if not filename + ".png" in files:
                            break
                    resp = self._request('get', img['datapoint_uri'], proxy=False)
                    with open(f'./imgs/{filename}.png', 'wb') as f:
                        f.write(resp.content)
            except:
                pass

if __name__ == "__main__":
    s = requests.session()
    # s.proxies.update({"http": "proxy", 'https': "proxy"}) # Proxies are recommended for bulk collection due to restrictions on requests

    HcaptchaCollector(s, 5).collect('site key', 'host')  # Ex.'4c672d35-0701-42b2-88c3-78380b0db560', 'discord.com'