from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import nodriver as uc
from pyvirtualdisplay import Display
import asyncio
import time

load_dotenv()
client = genai.Client()


async def summary_doi(doi: str):
    max_retries = 10
    for retry in range(max_retries):
        print(f"Attempt: {retry + 1}")
        try:
            display = None
            browser = None

            if os.getenv("LINUX") == "yes":
                display = Display(visible=0, size=(1920, 1080))
                display.start()

            browser = await uc.start(
                headless=False,
                # user_data_dir= os.getcwd() + "/profile", # by specifying it, it won't be automatically cleaned up when finished
                # browser_executable_path="/path/to/some/other/browser",
                # browser_args=['--some-browser-arg=true', '--some-other-option'],
                lang="en-US",  # this could set iso-language-code in navigator, it was not recommended to change according to docs
                no_sandbox=True,
            )
            tab = await browser.get(f"https://doi.org/{doi}")
            await tab.wait(2)
            await tab.select("body")  # waits for page to render first

            await tab.scroll_down(200)

            # body_text = await tab.get_all_urls()
            body_text = await tab.get_content()

            await tab.close()
            browser.stop()

            if display:
                display.stop()
            break
        except Exception as e:
            if browser:
                browser.stop()
                print(e)
            if display:
                display.stop()
                print(e)

    # Prompt
    prompt = f"""
        Summarize this publication in maximum 2 sentences and 300 characters for someone who may be interested in 
        reading further, ignore HTML: {body_text}
    """
    max_retries = 10
    response = None
    for retry in range(max_retries):
        print(f"Attempt: {retry + 1}")
        try:
            # Generate content
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert in cancer research",
                    temperature=0.5,
                ),
            )
            break
        except Exception as e:
            print(e)

        time.sleep(1)

    return response.text


async def summary_html(body_text: str):
    # Prompt
    prompt = f"""
        Summarize this publication in maximum 2 sentences and 300 characters for someone who may be interested in 
        reading further, ignore HTML: {body_text}
    """
    max_retries = 10
    response = None
    for retry in range(max_retries):
        print(f"Attempt: {retry + 1}")
        try:
            # Generate content
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert in cancer research",
                    temperature=0.5,
                ),
            )
            break
        except Exception as e:
            print(e)

        time.sleep(1)

    return response.text


async def main():
    await summary_doi("10.1038/s41598-025-20812-1")


if __name__ == "__main__":
    asyncio.run(main())
