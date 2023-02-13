import logging
import random
from typing import Optional
from datetime import datetime
import pandas as pd

from scrape.dir import change_dir


def export(dataframe: Optional[pd.DataFrame], export_dir: str):
    now = datetime.now()
    date = now.strftime("%y%m%d")

    with change_dir(export_dir):
        print_id = random.randint(0, 100)
        export_name = f"{date}_DIMScrape_Refactor_{print_id}.csv"
        msg_spreadsheetexported = f"\n[sciscraper]: A spreadsheet was exported as {export_name} in {export_dir}.\n"
        dataframe.to_csv(export_name)
        print(dataframe.head())
        logging.info(msg_spreadsheetexported)
        print(msg_spreadsheetexported)
