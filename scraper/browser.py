from datetime import datetime
from playwright.sync_api import *


#
#   Open with Playwright,
#
def open( url : str, proxy : str = "socks5://127.0.0.1:9050", headless : bool = True ) -> str | None:
    """
    Uses playwright to fetch the HTML from a given url.
    
    TODO: Handle CloudFlare and other CHAPTCHA.
    
    Args:
        url (str): The url to scrape
    
    Optional args:
        proxy (str):     Proxy to use
        headless (bool): Whether or not you want to use the browser as headless
        
    Returns:
        str: the html of the page. 
    """
    html : str = None
    
    printl(f"[✈] Using Playwright to navigate to { url } ...")
    with sync_playwright() as p:
        # Open Browser
        browser = p.chromium.launch( headless = headless )
        context = browser.new_context(
            proxy = { "server" : proxy },
            ignore_https_errors=True
        )
        
        # Navigate to the page
        page = context.new_page()
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")
        html = page.content()
        
    # Done! 
    printl("[✓] Page loaded. ")
    return html


# Helper functions.
def stamp(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def printl( string ): print( f"[{ stamp() }][{ __name__ }]" + string )
