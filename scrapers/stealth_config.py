"""
Shared stealth/anti-detection configuration for all scrapers.
Provides: user-agent rotation, realistic browser contexts, human-like delays,
stealth launch args, and per-page stealth evasion scripts.

Uses manual init scripts for stealth — no wrapper dependency, safe for parallel use.
"""

import random
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

_stealth_instance = Stealth()

# --- User-Agent Pool (Chrome ONLY — must match Chromium engine) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]

# --- Viewport Presets (common real resolutions) ---
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]

# --- Stealth Launch Args ---
STEALTH_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-component-update',
]

# --- Stealth Evasion Script (DEPRECATED - Moved to playwright-stealth) ---
# Custom script injections like toDataURL overrides trigger Datadome canvas locks.


def get_random_user_agent():
    """Return a random Chrome user-agent string."""
    return random.choice(USER_AGENTS)


def get_random_viewport():
    """Return a random realistic viewport dict."""
    return random.choice(VIEWPORTS)


async def human_delay(base_ms=1500, jitter_ms=500):
    """Sleep for base_ms ± jitter_ms to simulate human timing."""
    delay = max(100, base_ms + random.randint(-jitter_ms, jitter_ms))
    await asyncio.sleep(delay / 1000)


def get_context_options(locale="en-GB", timezone="Europe/London"):
    """
    Return a dict of options for browser.new_context() that make
    the browser look like a real user session.
    """
    ua = get_random_user_agent()
    vp = get_random_viewport()
    return {
        "user_agent": ua,
        "viewport": vp,
        "locale": locale,
        "timezone_id": timezone,
        "extra_http_headers": {
            "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
        },
    }


async def apply_stealth(page):
    """Apply all stealth evasion scripts to a page. Call after new_page()."""
    await _stealth_instance.apply_stealth_async(page)


async def human_scroll(page, scroll_count=None, scroll_min=300, scroll_max=800, delay_base=1200, delay_jitter=600):
    """
    Scroll the page in a human-like pattern with random distances and timing.
    """
    if scroll_count is None:
        scroll_count = random.randint(8, 14)

    for _ in range(scroll_count):
        scroll_amount = random.randint(scroll_min, scroll_max)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await human_delay(delay_base, delay_jitter)
