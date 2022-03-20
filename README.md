# Hcaptcha-Collector
Hcapcha image collector for artificial intelligence


## Use
```
import hcollector, requests

s = requests.session()
# s.proxies.update({"http": "proxy", 'https': "proxy"}) # Proxies are recommended for bulk collection due to restrictions on requests

hcollector.HcaptchaCollector(s, 5).collect("site key", 'url')  # Ex. '4c672d35-0701-42b2-88c3-78380b0db560', 'discord.com'
```
