import asyncio
import os
import json
from playwright.async_api import async_playwright
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class InventoryDataExtractor:
    def __init__(self, headless=False):
        self.headless = headless
        self.base_url = "https://hiring.idenhq.com/"
        self.username = "aaryasawant2545@gmail.com"
        self.password = "m1SSf4wg"  # Replace with your actual password
        self.session_file = "session_data.json"
        self.output_file = f"product_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    async def run(self):
        """Main execution method"""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.headless)
            # Increase default timeout for all operations
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800}
                
            )
            
            # Try to use existing session if available
            session_loaded = await self.load_session(context)
            
            page = await context.new_page()
            await page.goto(self.base_url, wait_until="networkidle")
            
            # Check if we need to authenticate
            if not session_loaded or await self.is_login_page(page):
                logger.info("No valid session found. Authenticating...")
                await self.authenticate(page)
                await self.save_session(context)
            else:
                logger.info("Using existing session")
            
            # Launch the challenge (if needed)
            await self.launch_challenge(page)
            
            # Navigate to the product table
            await self.navigate_to_product_table(page)
            
            # Extract product data
            product_data = await self.extract_product_data(page)
            
            # Save data to JSON file
            self.save_to_json(product_data)
            
            await context.close()
            await browser.close()
            
            logger.info(f"Extraction complete. Data saved to {self.output_file}")
            return product_data

    async def load_session(self, context):
        """Load session from file if it exists"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, "r") as f:
                    storage_state = json.load(f)
                await context.set_storage_state(state=storage_state)
                logger.info("Session loaded from file")
                return True
        except Exception as e:
            logger.error(f"Failed to load session: {str(e)}")
        return False

    async def save_session(self, context):
        """Save current session to file"""
        try:
            storage_state = await context.storage_state()
            with open(self.session_file, "w") as f:
                json.dump(storage_state, f)
            logger.info("Session saved to file")
        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")

    async def is_login_page(self, page):
        """Check if current page is the login page"""
        try:
            # Wait for short time to see if login form is visible
            login_form = await page.wait_for_selector("input[type='email']", timeout=5000)
            return login_form is not None
        except:
            return False

    async def authenticate(self, page):
        """Authenticate with the application"""
        try:
            logger.info("Authenticating...")
            # Wait for login form elements
            await page.wait_for_selector("input[type='email']", state="visible")
            await page.wait_for_selector("input[type='password']", state="visible")
            
            # Fill email and password
            await page.fill("input[type='email']", self.username)
            await page.fill("input[type='password']", self.password)
            
            # Click login button and wait for navigation
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")
            
            logger.info("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise

    async def launch_challenge(self, page):
        """Launch the challenge if necessary"""
        try:
            logger.info("Launching challenge...")
            # Check if there's a Launch Challenge button and click it
            try:
                launch_button = await page.wait_for_selector("button:has-text('Launch Challenge')", state="visible", timeout=10000)
                if launch_button:
                    await launch_button.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(5000)  # Added longer wait time to ensure page loads fully
                    logger.info("Challenge launched successfully")
            except Exception as e:
                logger.info(f"No launch button found or already in challenge: {str(e)}")
                # This is not necessarily an error, might already be in the challenge
        except Exception as e:
            logger.warning(f"Issue during challenge launch: {str(e)}")

    async def navigate_to_product_table(self, page):
        """Navigate through the application to the product table"""
        try:
            logger.info("Navigating to product table...")
            
            # First ensure the page is fully loaded
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)  # Wait for page to stabilize
            
            # Click 'Open Options' button
            open_options_selector = [
                "button:has-text('Open Options')",
                "[data-testid='open-options']",
                "button:text-is('Open Options')"
            ]
            
            # Try multiple selectors for the Open Options button
            for selector in open_options_selector:
                try:
                    open_options_button = await page.wait_for_selector(selector, state="visible", timeout=10000)
                    if open_options_button:
                        await open_options_button.click()
                        logger.info(f"Clicked Open Options button using selector: {selector}")
                        break
                except Exception:
                    continue
            
            # Wait for modal animation and click 'Inventory' tab
            await page.wait_for_timeout(3000)  # Wait longer for modal to appear
            inventory_selectors = [
                "button:has-text('Inventory')",
                "[data-testid='inventory-tab']",
                "button:text-is('Inventory')",
                "div[role='dialog'] button:has-text('Inventory')"
            ]
            
            # Try multiple selectors for Inventory tab
            for selector in inventory_selectors:
                try:
                    inventory_tab = await page.wait_for_selector(selector, state="visible", timeout=10000)
                    if inventory_tab:
                        await inventory_tab.click()
                        logger.info(f"Clicked Inventory tab using selector: {selector}")
                        break
                except Exception:
                    continue
            
            # Click 'Access Detailed View'
            await page.wait_for_timeout(3000)  # Wait longer for options to appear
            detailed_view_selectors = [
                "button:has-text('Access Detailed View')",
                "[data-testid='access-detailed-view']",
                "button:text-is('Access Detailed View')",
                "button >> text=Access Detailed View"
            ]
            
            # Try multiple selectors for Access Detailed View button
            for selector in detailed_view_selectors:
                try:
                    detailed_view_button = await page.wait_for_selector(selector, state="visible", timeout=12000)
                    if detailed_view_button:
                        await detailed_view_button.click()
                        logger.info(f"Clicked Access Detailed View button using selector: {selector}")
                        break
                except Exception:
                    continue
            
            # Check for detailed view selection if it appears
            await page.wait_for_timeout(3000)  # Wait longer for dialog to appear
            try:
                detailed_view_selectors = [
                    "div[role='dialog'] div:has-text('Detailed View')",
                    "[data-testid='detailed-view-option']",
                    "div:text-is('Detailed View')"
                ]
                
                for selector in detailed_view_selectors:
                    try:
                        detailed_view_option = await page.wait_for_selector(selector, state="visible", timeout=8000)
                        if detailed_view_option:
                            await detailed_view_option.click()
                            logger.info(f"Selected Detailed View option using selector: {selector}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                logger.info(f"No detailed view selection dialog found or already selected: {str(e)}")
            
            # Wait for the page to stabilize
            await page.wait_for_timeout(5000)
            await page.wait_for_load_state("networkidle")
            
            # Click 'Show Full Product Table' button with multiple potential selectors
            try:
                logger.info("Looking for Show Full Product Table button...")
                
                # Take a screenshot to help debug what's visible
                await page.screenshot(path="before_table_button.png")
                logger.info("Screenshot saved to before_table_button.png")
                
                # Try various selectors that might match the button
                show_table_selectors = [
                    "button:has-text('Show Full Product Table')",
                    "button:has-text('Product Table')",
                    "button:has-text('Show')",
                    "[data-testid='show-product-table']",
                    "button >> text=/.Product Table./",
                    "button >> text=/.Show.*Table./",
                    "button:text-is('Show Full Product Table')"
                ]
                
                button_found = False
                for selector in show_table_selectors:
                    try:
                        show_table_button = await page.wait_for_selector(selector, state="visible", timeout=8000)
                        if show_table_button:
                            await show_table_button.click()
                            logger.info(f"Clicked button using selector: {selector}")
                            button_found = True
                            break
                    except Exception:
                        continue
                
                if not button_found:
                    # If no button is found, try to find any visible buttons and log them
                    all_buttons = await page.query_selector_all("button:visible")
                    button_texts = []
                    for btn in all_buttons:
                        text = await btn.text_content()
                        button_texts.append(text.strip())
                    
                    logger.info(f"Available buttons on page: {button_texts}")
                    
                    # Try clicking a button that might be related to showing data
                    for btn, text in zip(all_buttons, button_texts):
                        if any(keyword in text.lower() for keyword in ["product", "table", "show", "data", "view", "inventory"]):
                            logger.info(f"Trying to click button with text: {text}")
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            break
            
            except Exception as e:
                logger.error(f"Issue with finding Show Full Product Table button: {str(e)}")
                
                # Take a screenshot to help debug
                await page.screenshot(path="debug_screenshot.png")
                logger.info("Debug screenshot saved to debug_screenshot.png")
                
                # Dump page content for debugging
                content = await page.content()
                with open("page_content.html", "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("Page content saved to page_content.html")
                
                # Instead of raising an exception, let's try to continue
                logger.info("Continuing with extraction despite button issues")
            
            # Wait for the table or any relevant content to be visible
            await page.wait_for_timeout(5000)  # Wait a bit longer to see what appears
            logger.info("Waiting for product data to load...")
            
            # Instead of waiting specifically for a table, capture whatever content is shown
            await page.wait_for_load_state("networkidle")
            logger.info("Page loaded, continuing to data extraction")
            
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            await page.screenshot(path="error_screenshot.png")
            logger.info("Error screenshot saved to error_screenshot.png")
            # Don't raise the exception, try to continue with extraction

    async def extract_product_data(self, page):
        """Extract all product data from the table or other container"""
        products = []
        
        try:
            logger.info("Extracting product data...")
            
            # Take a screenshot to see what we're working with
            await page.screenshot(path="before_extraction.png")
            logger.info("Page screenshot saved to before_extraction.png")
            
            # First, try to locate a table with multiple selectors
            table_selectors = ["table", ".product-table", "[role='table']", "div[data-type='table']"]
            table = None
            
            for selector in table_selectors:
                try:
                    table = await page.query_selector(selector)
                    if table:
                        logger.info(f"Found table using selector: {selector}")
                        break
                except:
                    continue
            
            if table:
                # Process table data
                logger.info("Found table, extracting data from it")
                
                # Get table headers to use as keys - try multiple approaches
                headers = []
                header_cell_selectors = [
                    "table thead th", 
                    "table th", 
                    "[role='table'] [role='columnheader']",
                    ".product-table .header-cell"
                ]
                
                for selector in header_cell_selectors:
                    try:
                        header_cells = await page.query_selector_all(selector)
                        if header_cells and len(header_cells) > 0:
                            for header_cell in header_cells:
                                header_text = await header_cell.text_content()
                                headers.append(header_text.strip())
                            logger.info(f"Found {len(headers)} headers: {headers}")
                            break
                    except:
                        continue
                
                # If no headers found, use default placeholder headers
                if not headers:
                    logger.info("No headers found, using placeholder headers")
                    headers = ["Column1", "Column2", "Column3", "Column4", "Column5", "Column6"]
                
                more_pages = True
                page_num = 1
                
                while more_pages:
                    logger.info(f"Processing page {page_num}...")
                    
                    # Try multiple selectors for table rows
                    row_selectors = [
                        "table tbody tr", 
                        "table tr:not(:first-child)", 
                        "[role='table'] [role='row']",
                        ".product-table .row"
                    ]
                    
                    rows = []
                    for selector in row_selectors:
                        try:
                            rows = await page.query_selector_all(selector)
                            if rows and len(rows) > 0:
                                logger.info(f"Found {len(rows)} rows using selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not rows:
                        logger.warning("No rows found in table")
                        break
                    
                    for row in rows:
                        product = {}
                        
                        # Try multiple selectors for cells
                        cell_selectors = ["td", "th", "[role='cell']", ".cell"]
                        cells = []
                        
                        for selector in cell_selectors:
                            try:
                                cells = await row.query_selector_all(selector)
                                if cells and len(cells) > 0:
                                    break
                            except:
                                continue
                        
                        for i, cell in enumerate(cells):
                            if i < len(headers):
                                cell_text = await cell.text_content()
                                product[headers[i]] = cell_text.strip()
                        
                        if product:  # Only add non-empty products
                            products.append(product)
                    
                    # Check if there's a next page button and it's enabled
                    try:
                        # Try multiple selectors for next button
                        next_button_selectors = [
                            "button:has-text('Next')", 
                            "[aria-label='Next Page']",
                            "button.next-page", 
                            "button >> text=Next"
                        ]
                        
                        next_button = None
                        for selector in next_button_selectors:
                            try:
                                next_button = await page.query_selector(selector)
                                if next_button:
                                    break
                            except:
                                continue
                        
                        if next_button:
                            # Check if button is disabled
                            is_disabled = await next_button.get_attribute("disabled")
                            aria_disabled = await next_button.get_attribute("aria-disabled")
                            
                            if not is_disabled and aria_disabled != "true":
                                await next_button.click()
                                await page.wait_for_load_state("networkidle")
                                await page.wait_for_timeout(2000)  # Wait for table to update
                                page_num += 1
                            else:
                                more_pages = False
                                logger.info("Next button is disabled, no more pages")
                        else:
                            more_pages = False
                            logger.info("No next button found, no more pages")
                    except Exception as e:
                        more_pages = False
                        logger.info(f"Error checking for next page: {str(e)}")
                
                logger.info(f"Extracted {len(products)} products from {page_num} pages")
            else:
                # If no table is found, try to extract from cards/divs or other elements
                logger.info("No table found, looking for alternative product elements")
                
                # Try to find product cards or other elements with multiple selectors
                product_selectors = [
                    "div[class*='product']", 
                    "div[class*='item']", 
                    "div[class*='card']",
                    ".product-card",
                    ".item-container",
                    "[data-type='product']"
                ]
                
                product_elements = []
                for selector in product_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            product_elements = elements
                            logger.info(f"Found {len(elements)} product elements using selector: {selector}")
                            break
                    except:
                        continue
                
                if product_elements:
                    for element in product_elements:
                        product = {}
                        
                        # Try to extract various fields based on common patterns
                        try:
                            name_selectors = ["h2", "h3", "div[class*='name']", "div[class*='title']", ".product-name", ".item-title"]
                            for selector in name_selectors:
                                name_element = await element.query_selector(selector)
                                if name_element:
                                    product["Name"] = await name_element.text_content()
                                    break
                            
                            price_selectors = ["div[class*='price']", "span[class*='price']", ".product-price", ".price"]
                            for selector in price_selectors:
                                price_element = await element.query_selector(selector)
                                if price_element:
                                    product["Price"] = await price_element.text_content()
                                    break
                            
                            # Try to get SKU or ID
                            id_selectors = ["div[class*='sku']", "div[class*='id']", ".product-id", ".sku"]
                            for selector in id_selectors:
                                id_element = await element.query_selector(selector)
                                if id_element:
                                    product["ID"] = await id_element.text_content()
                                    break
                            
                            # Extract all text content if nothing else was found
                            if not product:
                                product["Content"] = await element.text_content()
                            
                            products.append(product)
                        except Exception as e:
                            logger.error(f"Error extracting product data: {str(e)}")
                else:
                    # Last resort: try to get all text content from potential product-related elements
                    logger.info("No specific product elements found, trying to extract content from page sections")
                    
                    # Try to find divs that might contain product information
                    content_selectors = [
                        "div[class*='container']",
                        "div[class*='content']",
                        "div[class*='inventory']",
                        "main",
                        "section"
                    ]
                    
                    for selector in content_selectors:
                        try:
                            content_divs = await page.query_selector_all(selector)
                            if content_divs and len(content_divs) > 0:
                                for i, div in enumerate(content_divs):
                                    text = await div.text_content()
                                    # Only include divs with meaningful content
                                    if len(text.strip()) > 20:
                                        products.append({
                                            "Section": f"Content Section {i+1}",
                                            "Content": text.strip()
                                        })
                                
                                if products:
                                    logger.info(f"Extracted content from {len(products)} page sections")
                                    break
                        except:
                            continue
                    
                    # If still no products found, save the full page HTML
                    if not products:
                        content = await page.content()
                        products.append({"Content": "Page content extracted, see HTML file"})
                        
                        # Save the HTML for manual inspection
                        with open("product_page.html", "w", encoding="utf-8") as f:
                            f.write(content)
                        logger.info("Full page HTML saved to product_page.html")
        
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            await page.screenshot(path="extraction_error.png")
            # Don't raise the exception, return whatever we've extracted so far
        
        if not products:
            logger.warning("No products were extracted")
            products.append({"Error": "No products found", "Timestamp": datetime.now().isoformat()})
            
        return products

    def save_to_json(self, data):
        """Save extracted data to JSON file"""
        try:
            with open(self.output_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Data saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to save data to JSON: {str(e)}")
            raise

async def main():
    extractor = InventoryDataExtractor(headless=False)
    await extractor.run()

if __name__ == "__main__":
    asyncio.run(main())
