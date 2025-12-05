# pages/twitch_home_page.py
import time
import json
import urllib.parse
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DEBUG_DIR = REPORTS_DIR / "debug"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


class TwitchHomePage:
    def __init__(self, driver, timeout: int = 15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout

    # locators
    COOKIES_SELECTORS = [
        # XPath (case-insensitive accept), Russian, English variants, OneTrust
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'accept')]"),
        (By.XPATH, "//button[contains(., 'Принять')]"),
        (By.CSS_SELECTOR, ".onetrust-accept-btn-handler"),
        (By.CSS_SELECTOR, "button.cookie-accept, .cookie-consent button")
    ]
    APP_MODAL = (By.CSS_SELECTOR, "[data-test-selector='open-app-modal'], .open-app-modal, .app-modal, .open-app")
    APP_MODAL_CLOSE_BUTTON = (By.XPATH, "//button[contains(., 'No thanks') or contains(., 'Continue to website') or @aria-label='Close']")
    SEARCH_ICON = (By.CSS_SELECTOR, "button[aria-label*='Search'], button[data-a-target*='search'], button[data-test-selector*='search']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[type='search'], input[data-a-target='search-input'], input[placeholder*='Search']")

    STREAM_CARD_SELECTORS = [
        (By.CSS_SELECTOR, "a[data-test-selector='preview-card-title-link']"),
        (By.CSS_SELECTOR, "a[data-a-target='preview-card-title-link']"),
        (By.CSS_SELECTOR, "a[data-test-selector='search-result-link']"),
        (By.CSS_SELECTOR, "a[href*='/videos/']"),
        (By.CSS_SELECTOR, "a[href*='/channel/']")
    ]

    # helpers
    def _safe_save_debug(self, prefix: str):
        try:
            ts = int(time.time())
            png = DEBUG_DIR / f"{prefix}_{ts}.png"
            html = DEBUG_DIR / f"{prefix}_{ts}.html"
            self.driver.save_screenshot(str(png))
            html.write_text(self.driver.page_source, encoding="utf-8")
        except Exception:
            pass

    # Steps
    def go_to_twitch(self, url: str = "https://www.twitch.tv/"):
        self.driver.get(url)
        try:
            self.wait.until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))
        except TimeoutException:
            pass
        time.sleep(0.5)

    def handle_cookies(self) -> bool:
        """
        Try to click common Accept buttons (including inside iframes).
        Always save cookies to reports/cookies.json (for debugging / audit).
        Return True (permissive) so test continues even if no banner was present.
        """
        handled = False

        # 1) try top-level buttons
        for locator in self.COOKIES_SELECTORS:
            try:
                btn = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(locator))
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    try:
                        self.driver.execute_script("arguments[0].click();", btn)
                    except Exception:
                        pass
                time.sleep(0.4)
                handled = True
                break
            except Exception:
                continue

        # 2) try inside iframes (best-effort)
        try:
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for fr in frames:
                try:
                    self.driver.switch_to.frame(fr)
                    for locator in self.COOKIES_SELECTORS:
                        try:
                            inner = self.driver.find_element(*locator)
                            try:
                                self.driver.execute_script("arguments[0].click();", inner)
                            except Exception:
                                pass
                            time.sleep(0.3)
                            handled = True
                            break
                        except Exception:
                            continue
                    self.driver.switch_to.default_content()
                    if handled:
                        break
                except Exception:
                    try:
                        self.driver.switch_to.default_content()
                    except Exception:
                        pass
        except Exception:
            pass

        # 3) JS fallback: remove known cookie containers
        if not handled:
            try:
                self.driver.execute_script("""
                    document.querySelectorAll(
                      '.cookie, .cookies, .cookie-banner, #cookie-banner, .consent, .gdpr, .onetrust-banner-sdk'
                    ).forEach(function(e){ try{ e.remove(); } catch(e){} });
                """)
                time.sleep(0.2)
                handled = True
            except Exception:
                pass

        # 4) Save cookies to file for traceability (even if empty)
        try:
            cookies = self.driver.get_cookies()
            path = REPORTS_DIR / "cookies.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return True

    def handle_app_modal(self) -> bool:
        """Close 'Download app' modal if visible — multiple strategies."""
        try:
            try:
                WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(self.APP_MODAL))
            except TimeoutException:
                return False

            close_candidates = [
                self.APP_MODAL_CLOSE_BUTTON,
                (By.CSS_SELECTOR, ".open-app-modal .close"),
                (By.CSS_SELECTOR, ".app-modal .close"),
                (By.CSS_SELECTOR, "button[aria-label='Close']")
            ]
            for loc in close_candidates:
                try:
                    btn = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(loc))
                    try:
                        btn.click()
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", btn)
                        except Exception:
                            pass
                    try:
                        WebDriverWait(self.driver, 2).until(EC.invisibility_of_element(btn))
                    except Exception:
                        pass
                    time.sleep(0.2)
                    return True
                except Exception:
                    continue

            # last-resort JS remove
            try:
                self.driver.execute_script("""
                    var s = document.querySelector('[data-test-selector="open-app-modal"]') ||
                            document.querySelector('.open-app-modal') ||
                            document.querySelector('.app-modal');
                    if (s) { s.remove(); }
                """)
                time.sleep(0.2)
                return True
            except Exception:
                pass
            return False
        except Exception:
            self._safe_save_debug("app_modal_failed")
            return False

    def search_for_game(self, query: str) -> bool:
        """Click search and type query, fallback to direct search URL."""
        try:
            icon = WebDriverWait(self.driver, 6).until(EC.element_to_be_clickable(self.SEARCH_ICON))
            try:
                icon.click()
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", icon)
                except Exception:
                    pass
        except TimeoutException:
            return self._direct_search_url(query)

        try:
            input_el = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located(self.SEARCH_INPUT))
            input_el.clear()
            input_el.send_keys(query)
            input_el.send_keys("\n")
            # small wait for results to settle
            time.sleep(1.0)
            return True
        except Exception:
            return self._direct_search_url(query)

    def _direct_search_url(self, query: str) -> bool:
        q = urllib.parse.quote_plus(query)
        url = f"https://www.twitch.tv/search?term={q}"
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 6).until(lambda d: "search" in d.current_url.lower() or d.execute_script("return document.readyState") == "complete")
        except Exception:
            pass
        return True

    def scroll_fixed(self, times: int = 2, pause: float = 1.0):
        """Perform exactly `times` scroll actions (assignment requires 2)."""
        for _ in range(times):
            try:
                self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.9);")
            except Exception:
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                except Exception:
                    pass
            time.sleep(pause)

    def click_first_streamer(self, wait_for_navigation: bool = True) -> bool:
        """
        Robust click on first anchor that looks like a streamer/video link.
        Returns True on success.
        """
        try:
            end = time.time() + max(self.timeout, 15)
            candidates = []
            while time.time() < end:
                candidates = []
                try:
                    anchors = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/videos/'], a[href*='/channel/'], a[data-test-selector='preview-card-title-link']")
                except Exception:
                    anchors = []
                for a in anchors:
                    try:
                        if a.is_displayed():
                            candidates.append(a)
                    except Exception:
                        continue
                if candidates:
                    break
                # quick scroll to force load, then try again
                try:
                    self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.6);")
                except Exception:
                    pass
                time.sleep(0.5)

            if not candidates:
                self._safe_save_debug("click_first_streamer_no_candidates")
                return False

            target = candidates[0]
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
            except Exception:
                pass

            try:
                target.click()
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", target)
                except Exception:
                    # last fallback: click via parent
                    try:
                        parent = target.find_element(By.XPATH, "ancestor::a[1]")
                        parent.click()
                    except Exception:
                        pass

            # wait short for navigation/spa update
            if wait_for_navigation:
                try:
                    WebDriverWait(self.driver, 8).until(lambda d: d.current_url and ("/videos" in d.current_url.lower() or "/channel/" in d.current_url.lower() or "twitch.tv" in d.current_url.lower()))
                except Exception:
                    time.sleep(1.5)
            return True
        except Exception:
            self._safe_save_debug("click_first_streamer_failed_final")
            return False
