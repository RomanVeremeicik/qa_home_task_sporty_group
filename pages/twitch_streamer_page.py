# pages/twitch_streamer_page.py
import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR = REPORTS_DIR / "debug"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


class TwitchStreamerPage:
    def __init__(self, driver, timeout: int = 25):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout

    STREAMER_NAME = (By.CSS_SELECTOR, "[data-a-target='channel-name'], h1, .channel-info__username, .tw-title")
    STREAM_PLAYER = (By.CSS_SELECTOR, "video, [data-a-player-state], .video-player__container, [data-test-selector='video-player']")

    def wait_for_full_load(self, timeout: int = 20) -> bool:
        """Wait for player presence and (best-effort) streamer name visibility."""
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(self.STREAM_PLAYER))
            try:
                WebDriverWait(self.driver, 8).until(EC.visibility_of_element_located(self.STREAM_PLAYER))
            except Exception:
                pass
            try:
                WebDriverWait(self.driver, 6).until(EC.visibility_of_element_located(self.STREAMER_NAME))
            except Exception:
                pass
            time.sleep(1)
            return True
        except Exception:
            try:
                ts = int(time.time())
                png = DEBUG_DIR / f"stream_full_load_failed_{ts}.png"
                html = DEBUG_DIR / f"stream_full_load_failed_{ts}.html"
                self.driver.save_screenshot(str(png))
                html.write_text(self.driver.page_source, encoding="utf-8")
            except Exception:
                pass
            return False

    def get_streamer_name(self) -> str:
        try:
            el = self.wait.until(EC.visibility_of_element_located(self.STREAMER_NAME))
            return (el.text or "").strip()
        except Exception:
            try:
                return (self.driver.title or "").strip()
            except Exception:
                return ""

    def wait_for_video_playback(self, seconds: float = 5.0, timeout: int = 60) -> bool:
        """
        Wait until an HTML5 <video>'s currentTime advances by `seconds`.
        If no <video> element found, but player container exists, return True (best-effort).
        """
        get_current_time_js = "return (function(){ var v=document.querySelector('video'); return v? v.currentTime : null; })();"
        end = time.time() + timeout

        # wait for some player element
        try:
            WebDriverWait(self.driver, min(10, timeout)).until(
                lambda d: d.execute_script("return (document.querySelector('video')!==null) || (document.querySelector('[data-a-player-state]')!==null) || (document.querySelector('.video-player__container')!==null);")
            )
        except Exception:
            pass

        # initial read
        initial = None
        for _ in range(4):
            try:
                initial = self.driver.execute_script(get_current_time_js)
            except Exception:
                initial = None
            if initial is not None:
                break
            time.sleep(0.5)

        if initial is None:
            # fallback: treat presence of STREAM_PLAYER as success
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.STREAM_PLAYER))
                return True
            except Exception:
                return False

        # try to play if paused
        try:
            is_paused = self.driver.execute_script("var v=document.querySelector('video'); return v? v.paused : null;")
            if is_paused:
                try:
                    self.driver.execute_script("var v=document.querySelector('video'); if(v && v.paused) { try { v.play(); } catch(e){} }")
                except Exception:
                    pass
        except Exception:
            pass

        target = (initial or 0.0) + float(seconds)
        while time.time() < end:
            try:
                cur = self.driver.execute_script(get_current_time_js)
            except Exception:
                cur = None
            if cur is not None:
                try:
                    cur = float(cur)
                except Exception:
                    pass
                if cur >= target or cur >= float(seconds):
                    time.sleep(0.5)  # stabilization
                    return True
            time.sleep(0.4)
        return False

    def take_screenshot_after_playback(self, filename_prefix: str = "streamer", playback_seconds: float = 5.0, timeout: int = 60) -> str | None:
        """
        Wait for full load, observe playback for `playback_seconds`, take screenshot and return path.
        """
        try:
            # ensure page/player is present
            try:
                self.wait_for_full_load(timeout=max(8, timeout//3))
            except Exception:
                pass

            played = self.wait_for_video_playback(seconds=playback_seconds, timeout=timeout)
            # even if not observed, wait small stabilization
            if not played:
                time.sleep(1.5)

            ts = int(time.time())
            path = SCREENSHOTS_DIR / f"{filename_prefix}_{ts}.png"
            self.driver.save_screenshot(str(path))
            return str(path)
        except Exception:
            try:
                ts = int(time.time())
                fallback = SCREENSHOTS_DIR / f"{filename_prefix}_failed_{ts}.png"
                self.driver.save_screenshot(str(fallback))
                return str(fallback)
            except Exception:
                return None
