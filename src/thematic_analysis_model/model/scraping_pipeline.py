from thematic_analysis_model.model.dclasses import *
from thematic_analysis_model.model.util import *
from abc import ABC, abstractmethod
import codecs
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import uuid
import re

# UTILITY functions
# seed generator utility helps speed up process of generating seeds, which act as start nodes for the crawler to branch out from.
def generate_seeds(base: str, start: int, stop: int, end_seq: str) -> list[str]:
    seeds: list = []

    for i in range(start, stop + 1):
        seed: str = base + f'{i}' + end_seq
        seeds.append(seed)   

    return seeds

# can instantiate the scraping pipeline to be empty, however it will not run. It is on the user to ensure all data is prewsent to allow scraping pipeline to run.
class ScrapingPipeline(ABC):
    def __init__(self, seeds: list[str] | None = None, crawl_save_location: Path | None = None, scrape_save_location: Path | None = None, forum_origin: str | None = None):
        self.seeds = seeds
        self.crawl_save_location = crawl_save_location
        self.scrape_save_location = scrape_save_location
        self.forum_origin = forum_origin
        self.crawl_output = None
        self.scrape_output = None
        

    # main methods

    # run pipeline method
    def run_pipeline(self):
        # run crawler
        print('RUNNING CRAWLER')
        self.crawl_output = self.run_crawler()

        # optionally save scrape output
        if self.crawl_save_location: 
            self.save_crawl_output(self.crawl_output, self.crawl_save_location)

        print("RUNNING SCRAPER")
        # run scraper
        self.scrape_output = self.run_scraper()

        # optionally save scrape output
        if self.scrape_save_location: 
            self.save_scrape_output(self.scrape_output, self.scrape_save_location)

    # run_crawler method acts as 'queue' of all crawl operations to be performed on each 'seed' or start node
    # generate crawl output which is the list of all pages to be scraped from
    def run_crawler(self) -> list[str]:
        # iterate through seeds, to request each page html
        crawl_output = []

        for seed in self.seeds:
            output = self.crawl(seed)           
            crawl_output = crawl_output + output

        return crawl_output
    
    # run scraper method acts as 'queue', running many scraping operations for every link in the crawl output
    def run_scraper(self) -> list[Post] | None:
        print(1)
        scrape_output = []
        count = 0
        total = len(self.crawl_output)
        for crawl_seed in self.crawl_output:
            count += 1
            if count % 10 == 0:
                print(f'% {100*(count / total)} finished')
            try:
                scraped_post: Post = self.scrape(crawl_seed)
                if not ScrapingPipeline.validate_post(scraped_post): continue
                print(count)
                scrape_output.append(scraped_post)
            except Exception as e:
                print(f'ran into issue at {crawl_seed} exception: {e}')
            # validation step
        
        if not scrape_output: return None
        return scrape_output

      # scrape is a single scraping operation for a single link. It corresponds to the scraping of one single forum post.
    # is unique to each forum.
    def scrape(self, url: str) -> Post | None:
        # get page
        #TODO implement customization of header
        page_html = ScrapingPipeline.request_page(url)
        # get soup object
        soup = BeautifulSoup(page_html, 'html.parser')
        
        # get title
        title = self.scrape_title(soup)

        # get content
        content = self.scrape_content(soup)

        # get metadata
        # get unique id
        my_uuid = str(uuid.uuid4())

        #   get date
        date = self.scrape_date(soup)
        # get date accessed
        now = datetime.now()
        date_accessed = now.strftime("%Y-%m-%d %H:%M:%S")

        #   get author 
        #       get user name
        username = self.scrape_username(soup)       
        #       get user id
        userid = self.scrape_userid(soup)

        #   get comments: recursively call
        comments = self.scrape_comments(soup, url, self.forum_origin)

        # create objects, must package comments inside post object
        author = Author(username, userid)
        metadata = Metadata(my_uuid, author, url, date, self.forum_origin, str(date_accessed))
        post = Post(metadata, content, title, comments)

        return post

    # file i/o for seeds
    @classmethod
    def save_seeds(cls, seeds: list[str], fpath: Path):
        save_text(fpath, seeds)
    @classmethod
    def load_seeds(cls, fpath: Path) -> list[str]:
        return load_text(fpath)

    # file i/o for crawl output
    @classmethod
    def save_crawl_output(cls, crawl_output: list[str], fpath: Path):
        save_text(fpath=fpath, arr=crawl_output)
    @classmethod
    def load_crawl_output(cls, fpath) -> list[str]:
        return load_text(fpath)

    # file i/o for scrape output
    def save_scrape_output(cls, scrape_output: list[Post], fpath: Path):
        save_dclasses(file_path=fpath, cls=Post, dclasses=scrape_output)
    # NOT MEMORY EFFICIENT
    @classmethod
    def load_scrape_output(cls, fpath: Path) -> list[Post]:
        return load_dclasses(file_path=fpath, cls=Post)
    
    # request page
    # returns html of page as string
    # optionally pass in header, otherwise it uses default
    @classmethod
    def request_page(cls, url: str, header: dict = None) -> str:
        if not header:
            header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        try:
            response = requests.get(url, headers=header)
            if response.status_code == 200:
                ...
            else: print(f'REQUEST FAILED for {url}: ', response.status_code)

            html_text = response.text
            response.close() # close connection to server I think

            return html_text

        except requests.exceptions.RequestException as e:
            raise Exception(e)
    
    # method for processing text, and removing escape characterws
     # pre-process text
    @classmethod
    def process_text(cls, text):
        if not text:
            return None
        
        # two step decoding for double escape
        try:
            text = codecs.decode(text, 'unicode-escape') 
        except:
            pass
        for i in range(2):
            try:
                text = text.encode('latin-1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                break
            
        return text 

     # method validates post returning true if valid, false if not
    @classmethod
    def validate_post(self, post: Post) -> bool:
        # check post length (minimum characters)
        # check post title
        # check post meta data (*must have url, date, author?)
        #TODO implement duplicate checking

        if len(post.content) < 30: return False
        if not post.title: return False
        if not post.metadata.url: return False
        if not post.metadata.date: return False
        if not post.metadata.uuid: return False
        if not post.metadata.date_accessed: return False

        return True

    # validate comment method
    @classmethod
    def validate_comment(self, comment: Comment) -> bool:
        if len(comment.content) < 30: return False
        if not comment.metadata.url: return False
        if not comment.metadata.date: return False
        if not comment.metadata.uuid: return False
        if not comment.metadata.date_accessed: return False

        return True


    # splits posts into sentences, and writes them to file.
    @classmethod
    def process_sentences(cls, scrape_output: list[Post], fpath: Path, save_type: str = 'w'):
        # check current file length
        # if file does not exist, create it
        if save_type == 'w': count = 0
        elif save_type == 'a': 
            if os.path.exists(fpath):
                count = get_file_length(fpath)
            else: count = 0
        
        print(count)

        sentence_arr: list[dict] = []
        for post in scrape_output:
            for sentence in post.content.split('\n'):
                count += 1
                sentence_dict = {
                    'line_num': str(count),
                    'sentence': sentence.strip(),
                    'uuid': post.metadata.uuid
                }
                sentence_arr.append(sentence_dict)
        print(len(sentence_arr))
        sentence_json = [json.dumps(sentence) for sentence in sentence_arr]
        if save_type == 'w':
            save_text(fpath, sentence_json)
        elif save_type == 'a':
            append_text(fpath, sentence_json)

    # split scrape output into sentences
    # splits sentences from posts into their metadata, sentence, and line number of embedding
    @classmethod
    def split_sentences(cls, scrape_output: list[Post]) -> list[dict]:
        sentence_arr: list[dict] = []
        count = 0
        for post in scrape_output:
            for sentence in post.content.split('\n'):
                count += 1
                sentence_dict = {
                    'line_num': str(count),
                    'sentence': sentence.strip(),
                    'uuid': post.metadata.uuid
                }
                sentence_arr.append(sentence_dict)
        return sentence_arr
    
    # save sentences, either to existing file, or new one
    @classmethod
    def save_sentences(cls, sentences: list[dict], fpath: Path, save_type: str = 'w'):
        sentence_json = [json.dumps(sentence) for sentence in sentences]
        if save_type == 'a':
            append_text(fpath, sentence_json)
        elif save_type == 'w':
            save_text(fpath, sentence_json)
        


    
    # abstract methods for getting each componenet of the post: implemented by each specific scraping pipeline

    # crawl method is specific to each forum
    @abstractmethod
    def crawl(self, seed:str) -> list[str] | None:
        ...
    @abstractmethod
    def scrape_title(self, soup):
        ...
    # content will be stored as a string with newline characters separating sentences
    @abstractmethod
    def scrape_content(self, soup):
        ...
    @abstractmethod
    def scrape_date(self, soup):
        ...
    @abstractmethod
    def scrape_username(self, soup):
        ...
    @abstractmethod
    def scrape_userid(self, soup):
        ...
    # scrape comments plural
    #   must be able to return None if necessary
    @abstractmethod
    def scrape_comments(self, soup: BeautifulSoup, url: str, forum_origin: str) -> list[Comment] | None:
        ...


# ALZConnected.org specific scraping pipeline
class ALZConnectedScrapingPipeline(ScrapingPipeline):
    def __init__(self, seeds: list[str] = None, crawl_save_location: Path | str | None = None, scrape_save_location: Path | str | None = None, forum_origin = 'alzconnected'):
        super().__init__(seeds, crawl_save_location, scrape_save_location, forum_origin)

    
    # implement crawl indivudal page method
    def crawl(self, url: str) -> list[str] | None:
        html = ScrapingPipeline.request_page(url)
        if not html: return None

        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        for link in soup.find_all('a'):
            href = link.get('href')
            if '/discussion/' in href:
                links.add(href)

        return list(links)


    def scrape_title(self, soup: BeautifulSoup):
        title_text = soup.title.string
        title_text = title_text.removesuffix(' \u2014 ALZConnected') # '\u2014' is the em-dash escape key
        return title_text

    def scrape_content(self, soup: BeautifulSoup):
        div_discussion = soup.find('div', class_='Discussion') # discussion div
        div_content = div_discussion.find('div', class_='Message userContent') # get content out of discussion div
        if not div_content: return None 
        # get text and add separator for all separating elements in html
        content_unclean = div_content.get_text(separator=' ', strip=True)
        content_unclean = re.sub(r'\s+', ' ', content_unclean) # remove additional white space
        #TODO clean unicode characters
        decoded_text = ScrapingPipeline.process_text(content_unclean)

        content_split = re.sub(r'\. ', '.\n', decoded_text) # separate each sentence by period
        
        return content_split

    def scrape_date(self, soup: BeautifulSoup):
        div_date = soup.find('div', class_='Meta DiscussionMeta')       
        date = div_date.find('time').get('title')
        return date


    def scrape_username(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        username = div_author.find('a').text
        if not username: return None
        return username

    def scrape_userid(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        userid = div_author.find('a').get('data-userid')
        if not userid: return None
        return userid

    # scrape comments plural
    def scrape_comments(self, soup: BeautifulSoup, url: str, forum_origin: str) -> list[Comment] | None:
        # get list of soup objects for comments
        commentlist_div = soup.find('ul', class_='MessageList DataList Comments pageBox')
        # get each individual comment soup object from comment list
        if not commentlist_div: return None
        comments_div: list = commentlist_div.find_all('div', class_='Comment')

        comments = []
        # for each comment; scrape data
        for comment_div in comments_div:
            comment = self.scrape_comment(comment_div, url, forum_origin)
            if comment:
                comments.append(comment)

        if not comments: return None
        return comments
            
    # scrape individual comment
    def scrape_comment(self, soup: BeautifulSoup, url: str, forum_origin: str) -> Comment | None:
        # get comment data
        content = self.scrape_comment_content(soup)
        date = self.scrape_comment_date(soup)
        date_accessed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = self.scrape_comment_author_username(soup)
        userid = self.scrape_comment_author_userid(soup)
        author = Author(username, userid)
        my_uuid = str(uuid.uuid4())
        metadata = Metadata(my_uuid, author, url, date, forum_origin, date_accessed)
        #TODO figure out how to handle sub-comments of comments
        comment = Comment(metadata, content) 

        # validate comment
        if not ScrapingPipeline.validate_comment(comment): return None
        return comment
    
    # scrape content of comment, and do some initial cleaning of text
    def scrape_comment_content(self, soup: BeautifulSoup) -> str | None:
        div_content = soup.find('div', class_='Message userContent') # get content out of discussion div
        if not div_content: return None 
        # get text and add separator for all separating elements in html
        content_unclean = div_content.get_text(separator=' ', strip=True)
        if not content_unclean: return None

        content_clean = re.sub(r'\s+', ' ', content_unclean) # remove additional white space
        #TODO clean unicode characters
        content_split = re.sub(r'\. ', '.\n', content_clean) # separate each sentence by period

        return content_split
    def scrape_comment_date(self, soup: BeautifulSoup) -> str | None:
        date = soup.find('time').get('title')
        if not date: return None
        return date
    def scrape_comment_author_username(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        username = div_author.find('a').text
        if not username: return None
        return username
    def scrape_comment_author_userid(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        userid = div_author.find('a').get('data-userid')
        if not userid: return None
        return userid