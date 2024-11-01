import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from typing import List, Dict
import json


async def scrape_leetcode_patterns() -> List[Dict]:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            print("Creating new page...")
            page = await context.new_page()

            page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
            page.on("pageerror", lambda err: print(f"Browser error: {err}"))

            print("Accessing website...")
            await page.goto("https://neetcode.io/practice", wait_until="networkidle")

            print("Waiting for page to load...")
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_load_state("networkidle")

            print("Looking for NeetCode 150 tab...")

            try:
                print("Attempting to find and click the NeetCode 150 tab...")
                await page.evaluate("""() => {
                    const spans = Array.from(document.querySelectorAll('span'));
                    const targetSpan = spans.find(span => 
                        span.textContent.includes('🚀') && 
                        span.textContent.includes('NeetCode 150')
                    );
                    if (targetSpan) {
                        const parentButton = targetSpan.closest('button');
                        if (parentButton) {
                            parentButton.click();
                            return true;
                        }
                    }
                    throw new Error('NeetCode 150 tab not found');
                }""")

                print("Successfully clicked NeetCode 150 tab")
            except Exception as e:
                print(f"Error clicking tab: {str(e)}")
                raise

            print("Waiting for content to load...")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("networkidle")

            print("Extracting data...")
            patterns_data = await page.evaluate("""() => {
                const patterns = [];
                const sections = document.querySelectorAll('app-accordion');
                
                sections.forEach(section => {
                    try {
                        const paragraphs = section.querySelectorAll('p');
                        const patternName = paragraphs[0].textContent.trim();
                        const completion = paragraphs[1].textContent.trim();
                        
                        const problems = [];
                        const rows = section.querySelectorAll('tr.ng-star-inserted');
                        
                        rows.forEach(row => {
                            try {
                                const problemName = row.querySelector('a.table-text').textContent.trim();
                                const difficultyBtn = row.querySelector('button#diff-btn');
                                const difficulty = difficultyBtn ? difficultyBtn.textContent.trim() : 'Unknown';
                                const problemLink = row.querySelector('a.table-text').href;
                                
                                problems.push({
                                    name: problemName,
                                    difficulty: difficulty,
                                    url: problemLink
                                });
                            } catch (err) {
                                console.log('Error parsing row:', err);
                            }
                        });
                        
                        if (patternName && problems.length > 0) {
                            patterns.push({
                                pattern: patternName,
                                completion: completion,
                                problems: problems
                            });
                        }
                    } catch (err) {
                        console.log('Error parsing section:', err);
                    }
                });
                
                return patterns;
            }""")

            await browser.close()

            if not patterns_data:
                print("No patterns found in the extracted data")
            else:
                print(f"Successfully extracted {len(patterns_data)} patterns")

            return patterns_data

    except Exception as e:
        print(f"Unexpected error during scraping: {str(e)}")
        import traceback

        traceback.print_exc()
        return []


def save_to_csv(
    patterns_data: List[Dict], filename: str = "neetcode150_patterns.csv"
) -> bool:
    try:
        if not patterns_data:
            print("No data to save")
            return False

        flattened_data = []
        for pattern in patterns_data:
            for problem in pattern["problems"]:
                flattened_data.append(
                    {
                        "Pattern": pattern["pattern"],
                        "Completion": pattern["completion"],
                        "Problem": problem["name"],
                        "Difficulty": problem["difficulty"],
                        "URL": problem.get("url", ""),
                    }
                )

        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False)
        print(f"Data successfully saved to {filename}")

        with open("neetcode150_raw.json", "w") as f:
            json.dump(patterns_data, f, indent=2)
        print("Raw data saved to neetcode150_raw.json")

        return True

    except Exception as e:
        print(f"Error saving data to CSV: {str(e)}")
        return False


async def main():
    try:
        print("Starting web scraping...")
        patterns_data = await scrape_leetcode_patterns()

        if patterns_data:
            if save_to_csv(patterns_data):
                print("\nScraping Summary:")
                for pattern in patterns_data:
                    print(f"\n{pattern['pattern']} ({pattern['completion']}):")
                    for problem in pattern["problems"]:
                        print(f"- {problem['name']} ({problem['difficulty']})")
            else:
                print("Failed to save scraped data")
        else:
            print("No data was scraped")

    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
    finally:
        print("\nScript execution completed")


if __name__ == "__main__":
    asyncio.run(main())
