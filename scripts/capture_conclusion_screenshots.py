#!/usr/bin/env python3
"""
Screenshot Capture for Conclusion Node Testing

Captures screenshots demonstrating that conclusion nodes render correctly.
"""

import asyncio
import os
import sys
import time
import subprocess
import signal

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Install with: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)

# Output directory for screenshots
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_screenshots")
BASE_URL = "http://localhost:8501"

# Constants for graph interaction
CONCLUSION_NODE_VERTICAL_POSITION = 0.7  # Position from top where conclusion typically appears


async def wait_for_streamlit(page, timeout=10000):
    """Wait for Streamlit to be ready."""
    try:
        await page.wait_for_selector("text=Argument Graph Builder", timeout=timeout)
        await page.wait_for_timeout(2000)  # Additional stability wait
        return True
    except Exception as e:
        print(f"Failed to detect Streamlit: {e}")
        return False


async def capture_conclusion_screenshots():
    """Capture screenshots showing conclusion node rendering."""
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)  # Use headless=False to see what's happening
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        
        print(f"Connecting to {BASE_URL}...")
        
        try:
            # Navigate to app
            await page.goto(BASE_URL)
            
            # Wait for Streamlit to load
            if not await wait_for_streamlit(page):
                print("ERROR: Streamlit did not load properly")
                await browser.close()
                return False
            
            print("✓ Streamlit loaded")
            
            # Screenshot 1: Welcome screen
            print("Capturing: Welcome screen...")
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "1_welcome_screen.png"),
                full_page=False
            )
            
            # Load Conclusion Test example
            print("Loading Conclusion Test example...")
            
            # Click the dropdown
            dropdown = await page.query_selector('select:has-text("Load example text")')
            if dropdown:
                await dropdown.select_option(label="Conclusion Test")
                await page.wait_for_timeout(500)
            else:
                print("WARNING: Could not find dropdown")
            
            # Click Load Example button
            load_button = await page.query_selector('button:has-text("Load Example")')
            if load_button:
                await load_button.click()
                await page.wait_for_timeout(1000)
            else:
                print("WARNING: Could not find Load Example button")
            
            # Screenshot 2: After loading text
            print("Capturing: After loading text...")
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "2_text_loaded.png"),
                full_page=False
            )
            
            # Run extraction
            print("Running extraction...")
            extract_button = await page.query_selector('button:has-text("Run Extraction")')
            if extract_button:
                await extract_button.click()
                await page.wait_for_timeout(5000)  # Wait for extraction and graph rendering
            else:
                print("WARNING: Could not find Run Extraction button")
            
            # Screenshot 3: Graph with conclusion node
            print("Capturing: Graph with conclusion node...")
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "3_graph_with_conclusion.png"),
                full_page=False
            )
            
            # Try to click on the conclusion node (purple node)
            print("Attempting to select conclusion node...")
            await page.wait_for_timeout(2000)
            
            # Look for the graph canvas and click in the middle area where conclusion likely is
            # This is tricky because vis-network uses canvas, but we can try
            canvas = await page.query_selector('canvas')
            if canvas:
                # Click somewhere in the graph (this is approximate)
                box = await canvas.bounding_box()
                if box:
                    # Click near the bottom center where conclusion nodes typically appear
                    await page.mouse.click(
                        box['x'] + box['width'] / 2, 
                        box['y'] + box['height'] * CONCLUSION_NODE_VERTICAL_POSITION
                    )
                    await page.wait_for_timeout(1500)
            
            # Screenshot 4: Node details panel
            print("Capturing: Node details panel...")
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "4_conclusion_details.png"),
                full_page=False
            )
            
            # Check the legend includes conclusion
            print("Capturing: Legend with conclusion...")
            await page.screenshot(
                path=os.path.join(OUTPUT_DIR, "5_legend.png"),
                full_page=False
            )
            
            print("\n" + "=" * 60)
            print("✅ Screenshots captured successfully!")
            print("=" * 60)
            print(f"\nScreenshots saved to: {OUTPUT_DIR}")
            print("\nFiles:")
            for f in sorted(os.listdir(OUTPUT_DIR)):
                if f.endswith('.png'):
                    print(f"  - {f}")
            
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n❌ Error during screenshot capture: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()
            return False


def main():
    """Main entry point."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  CONCLUSION NODE RENDERING - SCREENSHOT CAPTURE        ║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Check if Streamlit is running
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8501))
    sock.close()
    
    streamlit_process = None
    
    if result != 0:
        print("Starting Streamlit app...")
        # Start Streamlit in background
        streamlit_process = subprocess.Popen(
            ["streamlit", "run", "app_mockup/app.py", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(os.path.dirname(__file__), "..")
        )
        # Wait for app to start
        time.sleep(10)
        print("✓ Streamlit started")
    else:
        print("✓ Streamlit already running")
    
    try:
        # Run async screenshot capture
        success = asyncio.run(capture_conclusion_screenshots())
        
        if success:
            print("\n✅ All screenshots captured successfully!")
            return 0
        else:
            print("\n❌ Screenshot capture failed")
            return 1
    
    finally:
        # Clean up Streamlit process
        if streamlit_process:
            print("\nStopping Streamlit...")
            streamlit_process.send_signal(signal.SIGTERM)
            streamlit_process.wait(timeout=5)
            print("✓ Streamlit stopped")


if __name__ == "__main__":
    sys.exit(main())
