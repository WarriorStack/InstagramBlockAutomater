from pathlib import Path

from playwright.sync_api import sync_playwright


PROFILE_DIR = Path(__file__).parent / "chrome_profile"


def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting Chrome login setup...")
    print(f"Profile directory: {PROFILE_DIR}")
    print()
    print("1. Chrome will open.")
    print("2. Log in manually.")
    print("3. Complete any verification required by Instagram.")
    print("4. Keep this window open until login is complete.")
    print("5. Return to this terminal and press Enter.")
    print()

    with sync_playwright() as p:

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            channel="chrome",
            viewport={
                "width": 1400,
                "height": 900,
            },
        )

        page = (
            context.pages[0]
            if context.pages
            else context.new_page()
        )

        page.goto(
            "https://www.instagram.com/",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        input(
            "\nPress Enter after you have finished logging in..."
        )

        context.close()

    print()
    print("Login setup completed.")
    print("The browser profile was saved locally.")
    print("You can now run: python app.py")


if __name__ == "__main__":
    main()