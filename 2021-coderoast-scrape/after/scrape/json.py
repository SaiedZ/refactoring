import json
import logging
import time
from json.decoder import JSONDecodeError
from scrape.scraper import ScrapeResult

import requests
from requests.exceptions import HTTPError, RequestException

KEYS = [
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
]


class JSONScrape:
    """The JSONScrape class takes the provided string from a prior list comprehension.
    Using that string value, it gets the resulting JSON data, parses it, and then returns a dictionary, which gets appended to a list.
    """

    def scrape(self, search_text: str) -> ScrapeResult:
        """The download method generates a session and a querystring that gets sent to the website. This returns a JSON entry.
        The JSON entry is loaded and specific values are identified for passing along, back to a dataframe.
        """
        self.sessions = requests.Session()
        search_field = "full_search" if search_text.startswith("pub") else "doi"
        self.base_url = URL_DMNSNS
        print(
            f"[sciscraper]: Searching for {search_text} via a {search_field}-style search.",
            end="\r",
        )
        querystring = {
            "search_mode": "content",
            "search_text": f"{search_text}",
            "search_type": "kws",
            "search_field": f"{search_field}",
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
                \n[sciscraper]: Proceeding to next item in sequence.\
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
            self.data = {_key: item.get(_key, "") for _key in KEYS}
        return self.data
