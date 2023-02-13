import logging
import os
import time
from contextlib import suppress

import requests
from bs4 import BeautifulSoup

from scrape.scraper import ScrapeResult


class SciHubScrape:
    """The SciHubScrape class takes the provided string from a prior list comprehension.
    Using that string value, it posts it to the selected website.
    Then, it downloads the ensuing pdf file that appears as a result of that query.
    """

    def scrape(self, search_text: str) -> ScrapeResult:
        """The download method generates a session and a payload that gets posted as a search query to the website.
        This search should return a pdf.
        Once the search is found, it is parsed with BeautifulSoup.
        Then, the link to download that pdf is isolated.
        """
        self.sessions = requests.Session()
        self.base_url = URL_SCIHUB
        print(
            f"[sciscraper]: Delving too greedily and too deep for download links for {search_text}, by means of dark and arcane magicx.",
            end="\r",
        )
        self.payload = {"request": f"{search_text}"}
        with change_dir(RESEARCH_DIR):
            time.sleep(1)
            with suppress(
                requests.exceptions.HTTPError, requests.exceptions.RequestException
            ):
                r = self.sessions.post(url=self.base_url, data=self.payload)
                r.raise_for_status()
                logging.info(r.status_code)
                soup = BeautifulSoup(r.text, "lxml")
                self.links = list(
                    ((item["onclick"]).split("=")[1]).strip("'")
                    for item in soup.select("button[onclick^='location.href=']")
                )
                self.enrich_scrape()

    def enrich_scrape(self, search_text: str):
        """With the link to download isolated, it is followed and thereby downloaded.
        It is sent as bytes to a temporary text file, as a middleman of sorts.
        The temporary text file is then used as a basis to generate a new pdf.
        The temporary text file is then deleted in preparation for the next pdf.
        """
        for link in self.links:
            paper_url = f"{link}=true"
            paper_title = f'{date}_{search_text.replace("/","")}.pdf'
            time.sleep(1)
            paper_content = (
                requests.get(paper_url, stream=True, allow_redirects=True)
            ).content
            with open("temp_file.txt", "wb") as _tempfile:
                _tempfile.write(paper_content)
            with open(paper_title, "wb") as file:
                for line in open("temp_file.txt", "rb").readlines():
                    file.write(line)
            os.remove("temp_file.txt")
