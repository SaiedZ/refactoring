import datetime
import json
import logging
import os
import random
import time
from contextlib import contextmanager, suppress
from json.decoder import JSONDecodeError
from os.path import isdir
from typing import Optional
from scrape.fetch import fetch_terms_from_pdf_files

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, RequestException
from tqdm import tqdm

# ==============================================
#    CONFIGS
# ==============================================

now = datetime.datetime.now()
date = now.strftime("%y%m%d")
export_dir = os.path.realpath("PDN Scraper Exports")
msg_error_1 = "[sciscraper]: HTTP Error Encountered, moving to next available object. Reason Given:"

logging.basicConfig(
    filename=f"{date}_scraper.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

PRIME_SRC = os.path.realpath("211001_PDN_studies_9.csv")
URL_DMNSNS = "https://app.dimensions.ai/discover/publication/results.json"
RESEARCH_DIR = os.path.realpath(f"{date}_PDN Research Papers From Scrape")
URL_SCIHUB = "https://sci-hubtw.hkvisa.net/"

# ==============================================
#    SCRAPE RELATED CLASSES & SUBCLASSES
# ==============================================


class ScrapeRequest:
    """The abstraction of the program's web scraping requests, which dynamically returns its appropriate subclasses based on the provided inputs."""

    _registry = {}

    def __init_subclass__(cls, slookup_code, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[slookup_code] = cls

    def __new__(cls, s_bool: bool):
        """The ScrapeRequest class looks for the boolean value passed to it from the FileRequest class.
        A value of True, or 1, would return a SciHubScrape subclass.
        Whereas a value of False, of 0, would return a JSONScrape subclass.
        """
        if not isinstance(s_bool, bool):
            raise TypeError
        if s_bool:
            slookup_code = "sci"
        else:
            slookup_code = "json"

        subclass = cls._registry[slookup_code]

        obj = object.__new__(subclass)
        return obj

    def download(self) -> None:
        raise NotImplementedError


class SciHubScrape(ScrapeRequest, slookup_code="sci"):
    """The SciHubScrape class takes the provided string from a prior list comprehension.
    Using that string value, it posts it to the selected website.
    Then, it downloads the ensuing pdf file that appears as a result of that query.
    """

    def download(self, search_text: str):
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


class JSONScrape(ScrapeRequest, slookup_code="json"):
    """The JSONScrape class takes the provided string from a prior list comprehension.
    Using that string value, it gets the resulting JSON data, parses it, and then returns a dictionary, which gets appended to a list.
    """

    def download(self, search_text: str) -> dict:
        """The download method generates a session and a querystring that gets sent to the website. This returns a JSON entry.
        The JSON entry is loaded and specific values are identified for passing along, back to a dataframe.
        """
        self.sessions = requests.Session()
        self.search_field = self.specify_search(search_text)
        self.base_url = URL_DMNSNS
        print(
            f"[sciscraper]: Searching for {search_text} via a {self.search_field}-style search.",
            end="\r",
        )
        querystring = {
            "search_mode": "content",
            "search_text": f"{search_text}",
            "search_type": "kws",
            "search_field": f"{self.search_field}",
        }
        time.sleep(1)

        try:
            r = self.sessions.get(self.base_url, params=querystring)
            r.raise_for_status()
            logging.info(r.status_code)
            self.docs = json.loads(r.text)["docs"]

        except (JSONDecodeError, RequestException) as e:
            print(
                f"\n[sciscraper]: An error occurred while searching for {search_text}.\
                \n\[sciscraper]: Proceeding to next item in sequence.\
                Cause of error: {e}\n"
            )
            pass

        except HTTPError as f:
            print(
                f"\n[sciscraper]: Access to {self.base_url} denied while searching for {search_text}.\
                \n[sciscraper]: Terminating sequence. Cause of error: {f}\
                \n"
            )
            quit()

        for item in self.docs:
            self.data = self.get_data_entry(
                item,
                keys=[
                    "title",
                    "author_list",
                    "publisher",
                    "pub_date",
                    "doi",
                    "id",
                    "abstract",
                    "acknowledgements",
                    "journal_title",
                    "volume",
                    "issue",
                    "times_cited",
                    "mesh_terms",
                    "cited_dimensions_ids",
                ],
            )
        return self.data

    def specify_search(self, search_text: str) -> str:
        """Determines whether the dimensions.ai query will be for a full_search or just for the doi."""
        if search_text.startswith("pub"):
            self.search_field = "full_search"
        else:
            self.search_field = "doi"
        return self.search_field

    def get_data_entry(self, item, keys: Optional[list]) -> dict:
        """Based on a provided list of keys and items in the JSON data,
        generates a dictionary entry.
        """
        return {_key: item.get(_key, "") for _key in keys}


# ==============================================
#    CONTEXT MANAGER METACLASS
# ==============================================


@contextmanager
def change_dir(destination: str):
    """Sets a destination for exported files."""
    try:
        __dest = os.path.realpath(destination)
        cwd = os.getcwd()
        if not os.path.exists(__dest):
            os.mkdir(__dest)
        os.chdir(__dest)
        yield
    finally:
        os.chdir(cwd)


# ==============================================
#    EXPORTING, MAIN LOOP, AND MISCELLANY
# ==============================================


def export(dataframe: Optional[pd.DataFrame]):
    with change_dir(export_dir):
        print_id = random.randint(0, 100)
        export_name = f"{date}_DIMScrape_Refactor_{print_id}.csv"
        msg_spreadsheetexported = f"\n[sciscraper]: A spreadsheet was exported as {export_name} in {export_dir}.\n"
        dataframe.to_csv(export_name)
        print(dataframe.head())
        logging.info(msg_spreadsheetexported)
        print(msg_spreadsheetexported)


def main():
    start = time.perf_counter()
    results = fetch_terms_from_pdf_files("../papers")
    export(results)
    elapsed = time.perf_counter() - start
    msg_timestamp = f"\n[sciscraper]: Extraction finished in {elapsed} seconds.\n"
    logging.info(msg_timestamp)
    print(msg_timestamp)
    quit()


if __name__ == "__main__":
    main()  # %%
