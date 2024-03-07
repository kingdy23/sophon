import asyncio
from playwright.async_api import async_playwright
import toml
import random
import re
import csv
from loguru import logger
from sys import stderr

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' - <level>{level: <8}</level>'
                          ' - <white>{message}</white>')


class AccountManager:
    def __init__(self):
        self.accounts = []

    async def create_account_file(self, filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["id", "proxy", "seed_phrase", "delay"])
            writer.writeheader()

    async def add_account(self, id, proxy, seed_phrase, delay):
        self.accounts.append({
            "id": id,
            "proxy": proxy,
            "seed_phrase": seed_phrase,
            "delay": delay,
            "status": "waiting"
        })

        with open("accounts.csv", "a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["id", "proxy", "seed_phrase", "delay", "status"])
            writer.writerow({
                "id": id,
                "proxy": proxy,
                "seed_phrase": seed_phrase,
                "delay": delay,
                "status": "waiting"
            })

    async def update_account_status(self, account_id, status):
        for account in self.accounts:
            if account["id"] == account_id:
                account["status"] = status
                break

        # Обновляем файл accounts.csv
        with open("accounts.csv", "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["id", "proxy", "seed_phrase", "delay", "status"])
            writer.writeheader()
            writer.writerows(self.accounts)

    async def load_data(self):
        config = toml.load("config.toml")
        sleep_before_account_min = config.get("SLEEP_BEFORE_ACCOUNT_MIN")
        sleep_before_account_max = config.get("SLEEP_BEFORE_ACCOUNT_MAX")

        with open("data/proxies.txt", "r") as file:
            proxies = [line.strip() for line in file.readlines() if line.strip() != ""]

        with open("data/seed_phrases.txt", "r") as file:
            seed_phrases = [line.strip() for line in file.readlines() if line.strip() != ""]

        for i in range(min(len(proxies), len(seed_phrases))):
            delay = random.randint(sleep_before_account_min, sleep_before_account_max)
            proxy = proxies[i]
            seed_phrase = seed_phrases[i] if i < len(seed_phrases) else None
            if seed_phrase:
                await self.add_account(i + 1, proxy, seed_phrase, delay)
                logger.info(f"Account {i + 1} will start working in {delay} seconds")
            else:
                logger.warning(f"No seed phrase found for proxy {proxy}. Skipping account {i + 1}")

    async def start_accounts(self):
        for account in self.accounts:
            await asyncio.sleep(account["delay"])
            await self.launch_browser(account)

    async def launch_browser(self, account):
        logger.info(f"Browser launched for account {account['id']}")

        proxy = account["proxy"]
        seed_phrase = account["seed_phrase"]

        config = toml.load("config.toml")
        user_agent = config.get("USER_AGENT")
        user_data_dir = ""
        path_to_extension = config.get("PATH_TO_EXTENSION")
        proxy_components = re.match(r'http://(.*):(.*)@(.*):(.*)', proxy).groups()

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,
                proxy={
                    "server": f"http://{proxy_components[2]}:{proxy_components[3]}",
                    "username": proxy_components[0],
                    "password": proxy_components[1]},
                args=[
                    f"--disable-extensions-except={path_to_extension}",
                    f"--load-extension={path_to_extension}",
                ],
                user_agent=user_agent
            )

            page_metamask = await context.new_page()

            await page_metamask.goto('chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#onboarding/welcome')

            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.wait_for_selector('#onboarding__terms-checkbox')
            await page_metamask.click('#onboarding__terms-checkbox')

            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.wait_for_selector('[data-testid="onboarding-import-wallet"]')
            await page_metamask.click('[data-testid="onboarding-import-wallet"]')

            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.wait_for_selector('[data-testid="metametrics-no-thanks"]')
            await page_metamask.click('[data-testid="metametrics-no-thanks"]')

            await asyncio.sleep(random.randint(2, 7))

            for i, word in enumerate(seed_phrase.split()):
                input_selector = f'[data-testid="import-srp__srp-word-{i}"]'
                await page_metamask.wait_for_selector(input_selector)
                await page_metamask.fill(input_selector, word)

            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.wait_for_selector('[data-testid="import-srp-confirm"]')
            await page_metamask.click('[data-testid="import-srp-confirm"]')

            await page_metamask.get_by_test_id("create-password-new").fill('11111111')
            await asyncio.sleep(random.randint(2, 7))
            await page_metamask.get_by_test_id("create-password-confirm").fill('11111111')
            await asyncio.sleep(random.randint(2, 7))
            await page_metamask.get_by_test_id("create-password-terms").click()
            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.click('[data-testid="create-password-import"]')

            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.click('[data-testid="onboarding-complete-done"]')

            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.click('[data-testid="pin-extension-next"]')

            await asyncio.sleep(random.randint(2, 7))

            await page_metamask.click('[data-testid="pin-extension-done"]')

            await asyncio.sleep(random.randint(2, 7))

            page_sophon = await context.new_page()
            await page_sophon.goto('https://sophon.xyz/')

            await asyncio.sleep(random.randint(2, 7))

            await page_sophon.click('.index_button__STkB1.index_button--enter__jghRN')

            await asyncio.sleep(random.randint(2, 7))

            await page_sophon.click('.connectWallet_connect-wallet-button__vI9Yp')

            await asyncio.sleep(random.randint(2, 7))

            await page_sophon.click('[data-testid="rk-wallet-option-io.metamask"]')

            async with context.expect_page() as new_page_info:
                new_page = await new_page_info.value

            await new_page.wait_for_load_state()

            await new_page.click('[data-testid="page-container-footer-next"]')

            await asyncio.sleep(random.randint(2, 7))

            await new_page.click('[data-testid="page-container-footer-next"]')
            await asyncio.sleep(random.randint(2, 7))

            await page_sophon.click('.index_button--top-right__Oy6mP')

            async with context.expect_page() as new_page_info:
                new_page = await new_page_info.value

            await asyncio.sleep(random.randint(2, 7))

            await new_page.click('[data-testid="page-container-footer-next"]')

            await asyncio.sleep(random.randint(2, 7))

            await context.close()

            await self.update_account_status(account["id"], "completed")


async def main():
    account_manager = AccountManager()
    await account_manager.create_account_file("accounts.csv")
    await account_manager.load_data()
    await account_manager.start_accounts()


asyncio.run(main())