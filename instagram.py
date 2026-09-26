from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import (
    sync_playwright,
    Error as PlaywrightError,
)

# Dedicated Chrome profile for this application.
PROFILE_DIR = Path(__file__).parent / "chrome_profile"

_playwright = None
_context = None
_page = None


def _is_alive():
    """Check whether stored Playwright objects are still usable."""
    try:
        if _context is None:
            return False

        if _context.pages is None:
            return False

        if _page is None or _page.is_closed():
            return False

        return True

    except Exception:
        return False


def start_browser():
    """Create or reuse one persistent Chrome session."""
    global _playwright, _context, _page

    if _is_alive():
        return _page

    close_browser()

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    _playwright = sync_playwright().start()

    try:
        _context = _playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            channel="chrome",
            viewport={"width": 1400, "height": 900},
        )

        if _context.pages:
            _page = _context.pages[0]
        else:
            _page = _context.new_page()

        return _page

    except Exception:
        close_browser()
        raise


def _process_profile(username):
    """
    Open profile and perform the existing block workflow.
    Returns:
        success
        failed
    """

    username = username.strip().lstrip("@").strip()

    if not username:
        return "failed"

    url = f"https://www.instagram.com/{quote(username)}/"

    page = start_browser()

    # 1. Open profile
    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    # 2. Find Options button
    options_button = page.get_by_role(
        "button",
        name="Options"
    )

    options_button.wait_for(
        state="visible",
        timeout=15000
    )

    options_button.click()

    # 3. Click Block
    block_button = page.get_by_role(
        "button",
        name="Block"
    )

    block_button.wait_for(
        state="visible",
        timeout=15000
    )

    block_button.click()

    # 4. Confirm Block
    confirm_block_button = page.get_by_role(
        "button",
        name="Block"
    )

    confirm_block_button.wait_for(
        state="visible",
        timeout=15000
    )

    confirm_block_button.click()

    # 5. Check confirmation dialog
    dialog = page.get_by_role("dialog")

    dialog.wait_for(
        state="visible",
        timeout=15000
    )

    popup_text = dialog.inner_text().lower()

    print("POPUP TEXT:")
    print(dialog.inner_text())

    if "blocked" in popup_text:

        print(f"SUCCESS: @{username}")

        # Dismiss dialog if available
        try:
            dismiss_button = dialog.get_by_role(
                "button",
                name="Dismiss"
            )

            dismiss_button.click(
                timeout=5000
            )

        except Exception:
            pass

        return "success"

    print(f"FAILED: @{username}")

    return "failed"


def open_profile(username):
    """
    Process one Instagram profile.
    Automatically retries once if Playwright fails.
    Always returns success or failed.
    """

    username = username.strip().lstrip("@").strip()

    if not username:
        return "failed"

    for attempt in range(2):

        try:

            print(
                f"Processing @{username} "
                f"(attempt {attempt + 1}/2)"
            )

            result = _process_profile(username)

            close_browser()

            return result

        except PlaywrightError as e:

            print(
                f"Playwright error for @{username}: {e}"
            )

            close_browser()

            if attempt == 1:
                print(
                    f"FAILED after retry: @{username}"
                )
                return "failed"

        except Exception as e:

            print(
                f"Unexpected error for @{username}: {e}"
            )

            close_browser()

            if attempt == 1:
                print(
                    f"FAILED after retry: @{username}"
                )
                return "failed"

    return "failed"


def close_browser():
    """Safely close Playwright browser and session."""
    global _playwright, _context, _page

    try:
        if _context is not None:
            _context.close()
    except Exception:
        pass

    try:
        if _playwright is not None:
            _playwright.stop()
    except Exception:
        pass

    _page = None
    _context = None
    _playwright = None