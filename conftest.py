"""Import/packages for pytest, selenium, requests and allure."""

import time
from pathlib import Path
import pytest
import requests
import allure
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

REPORTS_DIR = Path("reports")
ALLURE_RESULTS_DIR = REPORTS_DIR / "allure"
DEBUG_DIR = REPORTS_DIR / "debug"

for d in (REPORTS_DIR, ALLURE_RESULTS_DIR, DEBUG_DIR):
    d.mkdir(parents=True, exist_ok=True)

class ClientWrapper:
    """CLIENT WRAPPER (API)"""
    def __init__(self, session: requests.Session, timeout: int = 10):
        self.session = session
        self.timeout = timeout
        self.last_response = None

    def _request(self, method, url, **kwargs):
        """request method"""
        kwargs.setdefault("timeout", self.timeout)
        fn = getattr(self.session, method)
        r = fn(url, **kwargs)
        self.last_response = r
        return r

    def get(self, url, **kwargs):
        """GET METHOD"""
        return self._request("get", url, **kwargs)

    def post(self, url, **kwargs):
        """POST METHOD"""
        return self._request("post", url, **kwargs)

    def put(self, url, **kwargs):
        """PUT METHOD"""
        return self._request("put", url, **kwargs)

    def delete(self, url, **kwargs):
        """DELETE METHOD"""
        return self._request("delete", url, **kwargs)


@pytest.fixture(scope="session")
def client():
    """API CLIENT FIXTURE"""
    s = requests.Session()

    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({
        "User-Agent": "qa-tests",
        "Accept": "application/json",
    })

    wrapper = ClientWrapper(s)
    yield wrapper

    try:
        s.close()
    except ValueError:
        pass


@pytest.fixture(scope="function")
def driver():
    """DRIVER FIXTURE (MOBILE EMULATION) and IMPORTANT —
    Selenium Manager auto-installs correct ChromeDriver version"""

    chrome_options = Options()
    chrome_options.add_experimental_option("mobileEmulation", {
        "deviceName": "iPhone X"
    })

    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(375, 812)
    driver.implicitly_wait(3)

    yield driver

    try:
        driver.quit()
    except Exception:
        pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """PYTEST FAILURE → ATTACH LOGS TO ALLURE and attach API last response"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when != "call":
        return

    if rep.failed:
        client_fixture = item.funcargs.get("client", None)
        if client_fixture and client_fixture.last_response:
            resp = client_fixture.last_response

            try:
                allure.attach(resp.text, "last_response_body", allure.attachment_type.TEXT)
            except Exception:
                pass

        driver = item.funcargs.get("driver", None)
        if driver:
            try:
                ts = int(time.time())
                screenshot_path = DEBUG_DIR / f"{item.name}_{ts}.png"
                driver.save_screenshot(str(screenshot_path))
                allure.attach.file(
                    str(screenshot_path),
                    name="ui_screenshot",
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception:
                pass

        if call.excinfo:
            try:
                allure.attach(str(call.excinfo.value), "exception", allure.attachment_type.TEXT)
            except Exception:
                pass
