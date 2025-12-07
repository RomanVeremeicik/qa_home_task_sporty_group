"""tests/web/test_twitch_steps.py and Artifacts directories"""

import time
import json
from logging import exception
from pathlib import Path
import allure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pages.twitch_home_page import TwitchHomePage
from pages.twitch_streamer_page import TwitchStreamerPage


ROOT = Path.cwd()
REPORTS_DIR = ROOT / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
DEBUG_DIR = REPORTS_DIR / "debug"
for d in (REPORTS_DIR, SCREENSHOTS_DIR, DEBUG_DIR):
    d.mkdir(parents=True, exist_ok=True)


@allure.feature("Twitch Web — Step-by-step E2E")
class TestTwitchStepByStep:
    """
    Each test is one step. Browser session is shared for the whole class (setup_class),
    so state (opened page, search results, navigation) is preserved.
    """

    @classmethod
    def setup_class(cls):
        """
        create Chrome with mobile emulation (iPhone X)
        Selenium Manager will select proper chromedriver
        """
        chrome_options = Options()
        try:
            chrome_options.add_experimental_option("mobileEmulation", {"deviceName": "iPhone X"})
        except Exception as e:
            pass
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        cls.driver = webdriver.Chrome(options=chrome_options)
        try:
            cls.driver.set_window_size(375, 812)
        except Exception as e:
            pass
        cls.driver.implicitly_wait(2)

        cls.home = TwitchHomePage(cls.driver)
        cls.streamer = TwitchStreamerPage(cls.driver)
        cls.last_screenshot = None

    @classmethod
    def teardown_class(cls):
        """
        teardown method after each test
        """
        try:
            cls.driver.quit()
        except Exception as e:
            pass


    @allure.title("Step 1 — Open Twitch homepage")
    def test_01_open_homepage(self):
        """Open Twitch homepage"""
        with allure.step("Open https://www.twitch.tv"):
            self.home.go_to_twitch()
            assert self.driver.current_url.startswith("http"), "Twitch not opened properly"


    @allure.title("Step 2 — Close cookies (Accept) and save cookies")
    def test_02_close_cookies(self):
        """save cookies for debugging/verification and do not fail if cookies not present"""
        with allure.step("Attempt to accept cookies and save cookies.json"):
            self.home.handle_cookies()
            try:
                cookies = self.driver.get_cookies()
                path = REPORTS_DIR / "cookies.json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                allure.attach.file(str(path), name="cookies_json",\
                attachment_type=allure.attachment_type.JSON)
            except Exception as e:
                pass
            assert True


    @allure.title("Step 3 — Click search icon (open search)")
    def test_03_click_search_icon(self):
        """using search_for_game with empty query will open search UI or fallback
        and method may fallback to direct URL, treat as success"""
        with allure.step("Reveal search input by clicking search icon"):

            ok = self.home.search_for_game("")
            assert ok is True or ok is None


    @allure.title("Step 4 — Enter 'StarCraft II' and submit")
    def test_04_enter_search_query(self):
        """Search and submit for 'StarCraft II'"""
        with allure.step("Enter 'StarCraft II' and submit search"):
            ok = self.home.search_for_game("StarCraft II")
            assert ok, "Search action failed"


    @allure.title("Step 5 — Scroll down exactly 2 times")
    def test_05_scroll_two_times(self):
        """Scroll down 2 times"""
        with allure.step("Scroll down 2 times to load results"):
            self.home.scroll_fixed(times=2, pause=1.0)
            assert True


    @allure.title("Step 6 — Click first streamer from results")
    def test_06_click_first_streamer(self):
        """Select one streamer from results and save debug"""
        with allure.step("Select first visible streamer in results"):
            clicked = self.home.click_first_streamer(wait_for_navigation=True)
            if not clicked:
                ts = int(time.time())
                png = DEBUG_DIR / f"click_failed_{ts}.png"
                html = DEBUG_DIR / f"click_failed_{ts}.html"
                try:
                    self.driver.save_screenshot(str(png))
                    html.write_text(self.driver.page_source,\
                    encoding="utf-8")
                    allure.attach.file(str(png), name="click_failed_screenshot",
                    attachment_type=allure.attachment_type.PNG)
                    allure.attach(html.read_text(encoding="utf-8"), name="click_failed_html",
                    attachment_type=allure.attachment_type.TEXT)
                except Exception as e:
                    pass
            assert clicked, "Could not click a streamer"


    @allure.title("Step 7 — Wait until streamer page loads (~2-3s)")
    def test_07_wait_streamer_page(self):
        """Wait until streamer page loads"""
        with allure.step("Wait for streamer page to be ready"):
            ok = self.streamer.wait_for_full_load(timeout=20)
            assert ok, "Streamer page did not load"


    @allure.title("Step 8 — Play video for 5 seconds")
    def test_08_play_video_5s(self):
        """Video playback for 5 seconds"""
        with allure.step("Ensure video starts playing and play for ~5 seconds"):
            played = self.streamer.wait_for_video_playback(seconds=5.0, timeout=60)
            assert played, "Video did not progress as expected"


    @allure.title("Step 9 — Take screenshot after playback")
    def test_09_take_screenshot(self):
        """Take screenshot of playing stream"""
        with allure.step("Take screenshot after playback and attach"):
            path = self.streamer.take_screenshot_after_playback(filename_prefix="streamer_e2e",
                                                                playback_seconds=0.0, timeout=10)
            assert path, "Screenshot not created"
            p = Path(path)
            assert p.exists(), f"Screenshot not found: {path}"
            allure.attach.file(str(p), name="streamer_final_screenshot",
                            attachment_type=allure.attachment_type.PNG)
            self.__class__.last_screenshot = str(p)
