import asyncio
from thematic_analysis_model.config import *
from thematic_analysis_model.model.manage_data import Loader, CorpusManager
from thematic_analysis_model.model.scraping import ALZConnectedScrapingPipeline, DementiaSupportForumScrapingPipeline, Crawler
from thematic_analysis_model.model.dclasses import Line, Content

import pprint

def main():
    # load database
    loader = Loader(
        lance_path=LANCE_PATH,
        tbl1_name=CONTENT_TBL_NAME,
        tbl2_name=LINE_TBL_NAME
    )
    loader.first_init(schema1=Content, schema2=Line)
    db, ptbl, ltbl = loader.connect()
    print(ptbl.count_rows())



    



if __name__ == '__main__':
    try:
        main()
    except* Exception as eg:
        for exc in eg.exceptions:
            import traceback
            traceback.print_exception(type(exc), exc, exc.__traceback__)