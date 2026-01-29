#!/usr/bin/env python3
"""
Screenshot Capture Script for Milestone 2

This script uses Playwright to automatically capture screenshots of the
Argument Graph Builder prototype for documentation purposes.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    python scripts/capture_screenshots.py

Note: The Streamlit app must be running at http://localhost:8501 before
executing this script.
"""

import asyncio
import os
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Install with: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)

# Output directory for screenshots
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "milestones", "m2_screenshots")
BASE_URL = "http://localhost:8501"


async def capture_screenshots():
    """Capture all milestone screenshots."""
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        
        print(f"Connecting to {BASE_URL}...")
        
        try:
            # Task 1: Before extraction (welcome screen)
            await page.goto(BASE_URL)
            await page.wait_for_timeout(3000)  # Wait for Streamlit to load
            
            print("Capturing Task 1: Before extraction...")
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "task1_before.png"),
                full_page=True
            )
            
            # Load example text
            await page.get_by_role("combobox", name="Load example text").click()
            await page.get_by_role("option", name="Death Penalty Argument").click()
            await page.get_by_role("button", name="Load Example").click()
            await page.wait_for_timeout(1000)
            
            # Run extraction
            await page.get_by_role("button", name="Run Extraction").click()
            await page.wait_for_timeout(5000)  # Wait for extraction
            
            print("Capturing Task 1: After extraction...")
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "task1_after.png"),
                full_page=True
            )
            
            # Task 2: Select a node
            print("Capturing Task 2: Graph and node detail...")
            await page.get_by_role("combobox", name="Select a node to inspect").click()
            await page.get_by_role("option", name="Death penalty should be").click()
            await page.wait_for_timeout(1000)
            
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "task2_graph.png")
            )
            
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "task2_detail.png"),
                full_page=True
            )
            
            # Task 3: Q&A
            print("Capturing Task 3: Q&A interaction...")
            
            # Select nodes for Q&A
            await page.get_by_role("combobox", name="Select nodes for Q&A").click()
            await page.get_by_role("option", name="Deterrent effect claim").click()
            await page.get_by_role("option", name="No deterrent evidence").click()
            await page.keyboard.press("Escape")
            
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "task3_select.png"),
                full_page=True
            )
            
            # Switch to Q&A tab and ask question
            await page.get_by_role("tab", name="Q&A Panel").click()
            await page.get_by_role("textbox", name="Your question").fill(
                "Why doesn't the deterrence argument succeed?"
            )
            await page.keyboard.press("Enter")
            await page.get_by_role("button", name="Ask Question").click()
            await page.wait_for_timeout(1000)
            
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "task3_answer.png"),
                full_page=True
            )
            
            print(f"\nScreenshots saved to: {OUTPUT_DIR}")
            print("Files captured:")
            for f in sorted(os.listdir(OUTPUT_DIR)):
                if f.endswith(".png"):
                    print(f"  - {f}")
                    
        except Exception as e:
            print(f"Error capturing screenshots: {e}")
            print("\nMake sure the Streamlit app is running:")
            print("  streamlit run app_mockup/app.py")
            
        finally:
            await browser.close()


if __name__ == "__main__":
    print("Milestone 2 Screenshot Capture Script")
    print("=" * 40)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    asyncio.run(capture_screenshots())
