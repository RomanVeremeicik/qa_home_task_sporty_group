# tests/web/test_twitch_mobile_search.py
import time
from pages.twitch_home_page import TwitchHomePage
from pages.twitch_streamer_page import TwitchStreamerPage


def test_twitch_mobile_streamer_selection(driver):
    home = TwitchHomePage(driver)
    streamer_page = TwitchStreamerPage(driver)

    # A. Open main page
    home.go_to_twitch()

    # B. Close cookies
    home.handle_cookies()

    # C. Close app modal
    home.handle_app_modal()

    # short stabilization wait
    time.sleep(1.0)

    # D. Search for "StarCraft II"
    ok = home.search_for_game("StarCraft II")
    assert ok, "Search action failed (see debug_* files)"

    # E. Scroll down 2 times
    home.scroll_down(times=2, pause=1.0)

    # F. Click first streamer
    clicked = home.click_first_streamer()
    assert clicked, "Could not click first streamer (see debug_* files)"

    # Wait for stream player and verify streamer name visible
    streamer_page.wait_for_stream(timeout=12)
    name = streamer_page.get_streamer_name()
    assert name and len(name.strip()) > 0, "Streamer name not found"
    print("Streamer name:", name)
