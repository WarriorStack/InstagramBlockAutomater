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
    """Check whether our stored Playwright objects are still usable."""
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


def open_profile(username):
    """Open a profile and then click the Options button."""
    username = username.strip().lstrip("@").strip()

    if not username:
        return

    url = f"https://www.instagram.com/{quote(username)}/"

    try:
        page = start_browser()

        if page.is_closed():
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

        # 3. Wait for it
        options_button.wait_for(
            state="visible",
            timeout=15000
        )

        # 4. Click it
        options_button.click()


        #5. Clicking on block Button
        
        block_button = page.get_by_role("button", name="Block")
        block_button.wait_for(state="visible", timeout=15000)
        block_button.click()

        # Confirming Block
        block_button = page.get_by_role("button", name="Block")
        block_button.wait_for(state="visible", timeout=15000)
        block_button.click()

  
            # Wait for popup/dialog
        dialog = page.get_by_role("dialog")
        dialog.wait_for(state="visible", timeout=15000)

        # Print everything inside the popup
        print("POPUP TEXT:")
        print(dialog.inner_text())

        # Check whether the popup contains the expected result
        popup_text = dialog.inner_text().lower()

        if "blocked" in popup_text:
            print(f"SUCCESS: @{username}")
            result = "success"
        else:
            print(f"FAILED: @{username}")
            result = "failed"

        # Dismiss after verification
        dismiss_button = dialog.get_by_role("button", name="Dismiss")
        dismiss_button.click()

        close_browser()
        return result


    
    except PlaywrightError as e:
        print(f"Playwright error: {e}")

        try:
            close_browser()

            page = start_browser()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            options_button = page.get_by_role(
                "button",
                name="Options"
            )

            options_button.wait_for(
                state="visible",
                timeout=15000
            )

            options_button.click()

            print(f"Retry successful for @{username}")

        except Exception as retry_error:
            print(f"Retry failed: {retry_error}")


def close_browser():
    """Safely close the Playwright browser and session."""
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