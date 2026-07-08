from thematic_analysis_model.config import *
from thematic_analysis_model.model.manage_data import Loader, CorpusManager
from thematic_analysis_model.model.dclasses import Line, Content

def main():
    # load database
    loader = Loader(
        lance_path=LANCE_PATH,
        tbl1_name=CONTENT_TBL_NAME,
        tbl2_name=LINE_TBL_NAME
    )
    db, ptbl, ltbl = loader.connect()



if __name__ == '__main__':
    main()