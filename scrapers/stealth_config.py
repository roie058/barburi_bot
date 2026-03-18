"""
Shared stealth/anti-detection configuration for all scrapers.
Provides: user-agent rotation, realistic browser contexts, human-like delays,
stealth launch args, and per-page stealth evasion scripts.

Uses manual init scripts for stealth — no wrapper dependency, safe for parallel use.
"""

import random
import asyncio
from playwright.async_api import async_playwright

# --- User-Agent Pool (Chrome ONLY — must match Chromium engine) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
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

# --- Stealth Evasion Script (injected per-page via add_init_script) ---
STEALTH_INIT_SCRIPT = """
    // 1. Hide navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // 2. Fake chrome.runtime (Chromium detection)
    if (!window.chrome) { window.chrome = {}; }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: function() {},
            sendMessage: function() {}
        };
    }

    // 3. Fix Permissions API (notifications query leak)
    const originalQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
    window.navigator.permissions.query = (parameters) => {
        if (parameters.name === 'notifications') {
            return Promise.resolve({ state: Notification.permission });
        }
        return originalQuery(parameters);
    };

    // 4. Fix plugin array (headless Chrome has 0 plugins)
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' }
        ]
    });

    // 5. Fix languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-GB', 'en-US', 'en']
    });

    // 6. Canvas fingerprint noise
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        const ctx = this.getContext('2d');
        if (ctx && this.width > 0 && this.height > 0) {
            try {
                const imageData = ctx.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < Math.min(imageData.data.length, 40); i += 4) {
                    imageData.data[i] ^= 1;
                }
                ctx.putImageData(imageData, 0, 0);
            } catch(e) {}
        }
        return origToDataURL.apply(this, arguments);
    };
"""


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
    await page.add_init_script(STEALTH_INIT_SCRIPT)


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
