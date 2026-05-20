from thematic_analysis_model.model.scraping_pipeline import *
import pytest
import copy


# test seed generator
def test_generate_seeds():
    base = 'www.testWebsite/p'
    end_seq = '/testing.com'

    expected = [
        'www.testWebsite/p1/testing.com',
        'www.testWebsite/p2/testing.com',
        'www.testWebsite/p3/testing.com',
        'www.testWebsite/p4/testing.com',
        'www.testWebsite/p5/testing.com',
    ]
    expected2 = [
        'www.testWebsite/p10/testing.com',
        'www.testWebsite/p11/testing.com',
        'www.testWebsite/p12/testing.com',
        'www.testWebsite/p13/testing.com',
        'www.testWebsite/p14/testing.com',
    ]
    output = generate_seeds(base, 1, 5, end_seq)
    output2 = generate_seeds(base, 10, 14, end_seq)

    assert expected == output
    assert expected2 == output2

# test save and reading of seeds
def test_save_load_seeds():
    base = 'www.testWebsite/p'
    end_seq = '/testing.com'
    seeds = generate_seeds(base, 1, 5, end_seq)
    fpath = Path.cwd() / 'tests' / 'testing_data' / 'test_save_seeds.txt'

    # save seeds
    ScrapingPipeline.save_seeds(seeds, fpath)

    # laod seeds
    loaded_seeds = ScrapingPipeline.load_seeds(fpath)

    assert loaded_seeds == seeds

def test_post_validation():
    a = Author('username', '123')
    m = Metadata('really unique', a, 'test.com', 'today', 'forum', 'today')
    p = Post(m, 'content', 'title', None)

    invalid1 = copy.deepcopy(p)
    invalid2 = copy.deepcopy(p)
    invalid3 = copy.deepcopy(p)
    invalid4 = copy.deepcopy(p)
    invalid5 = copy.deepcopy(p)
    invalid6 = copy.deepcopy(p)

    invalid1.title = ""
    invalid2.content = 'too short'
    invalid3.metadata.url = ''
    invalid4.metadata.date = ''
    invalid5.metadata.uuid = ''
    invalid6.metadata.date_accessed = ''

    assert ScrapingPipeline.validate_post(invalid1) == False
    assert ScrapingPipeline.validate_post(invalid2) == False
    assert ScrapingPipeline.validate_post(invalid3) == False
    assert ScrapingPipeline.validate_post(invalid4) == False
    assert ScrapingPipeline.validate_post(invalid5) == False
    assert ScrapingPipeline.validate_post(invalid6) == False

def test_comment_validation():
    a = Author('username', '123')
    m = Metadata('really unique', a, 'test.com', 'today', 'forum', 'today')
    c = Comment(m, 'content', None)

    invalid1 = copy.deepcopy(c)
    invalid2 = copy.deepcopy(c)
    invalid3 = copy.deepcopy(c)
    invalid4 = copy.deepcopy(c)
    invalid5 = copy.deepcopy(c)

    invalid1.content = 'too short'
    invalid2.metadata.url = ''
    invalid3.metadata.date = ''
    invalid4.metadata.uuid = ''
    invalid5.metadata.date_accessed = ''

    assert ScrapingPipeline.validate_post(invalid1) == False
    assert ScrapingPipeline.validate_post(invalid2) == False
    assert ScrapingPipeline.validate_post(invalid3) == False
    assert ScrapingPipeline.validate_post(invalid4) == False
    assert ScrapingPipeline.validate_post(invalid5) == False

# testing ALZConnected.org crawler, using https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p10 as the seed
# note test written Monday 11th, May 2026 11:30 AM, so links may change. Keep this in mind if tests start to fail.
def test_ALZConnected_crawler():
    seed = ['https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p10']
    p = Path.cwd() / 'tests' / 'testing_data' / 'test_crawl_output.txt'

    pipeline = ALZConnectedScrapingPipeline(seeds=seed, crawl_save_location=p, scrape_save_location = None)   
    pipeline.crawl_output = pipeline.run_crawler()

    # set of posts as scraped Monday 11th, May 2026, 11:30AM
    expected_list = [
        'https://alzconnected.org/discussion/56167/friend-still-asking-why-me',
        'https://alzconnected.org/discussion/55782/free-on-line-activities',
        'https://alzconnected.org/discussion/55676/iris-9',
        'https://alzconnected.org/discussion/64407/common-abbreviations', 
        'https://alzconnected.org/discussion/56242/new-brain-guide',
        'https://alzconnected.org/discussion/64696/dementia-resources/',
        'https://alzconnected.org/discussion/55907/first-post-my-husband-may-have-dementia-and-i-am-terrified',
        'https://alzconnected.org/discussion/55236/another-one-of-my-podcast',
        'https://alzconnected.org/discussion/56285/australia-national-dementia-helpline',
        'https://alzconnected.org/discussion/55868/instagram-support-page',
        'https://alzconnected.org/discussion/56011/meghan-markle-suicidal-ideation-and-stigma',
        'https://alzconnected.org/discussion/55872/i-got-my-first-covid-19-vaccine',
        'https://alzconnected.org/discussion/56161/i-lost-my-covid-weight',
        'https://alzconnected.org/discussion/55910/using-poetry-as-an-outlet',
        'https://alzconnected.org/discussion/55630/benefit-of-therapist-or-psychologist-for-husband',
    ]
    expected_set = set(expected_list)

    assert set(pipeline.crawl_output) == expected_set



def test_ALZConnected_scraper_serialization():
    # scrape one post data: https://alzconnected.org/discussion/56167/friend-still-asking-why-me
    # scraped Tue May 12 2026, 2:00pm 
    crawl_input = [
        'https://alzconnected.org/discussion/56167/friend-still-asking-why-me',
        'https://alzconnected.org/discussion/75214/hoping-to-start-an-ongoing-conversation-space-for-those-living-with-dementia',
        'https://alzconnected.org/discussion/75017/early-onset-alzheimers-at-49'
                   ]

    # get scraper
    scraper = ALZConnectedScrapingPipeline()    
    scraper.crawl_output = crawl_input
    path = Path.cwd() / 'tests' / 'testing_data' / 'test_scrape_output.jsonl'
    scraper.scrape_save_location = path

    # run scraping pipeline 
    output = scraper.run_scraper()
    scraper.scrape_output = output

    # save to file
    scraper.save_scrape_output(scraper.scrape_output, path)

    # smart load
    posts = scraper.load_scrape_output(path)

    assert posts[0] == scraper.scrape_output[0]

def test_save_sentence():
    sentences = [
        {'line_number': 1, 'sentence': 'this is a sentence', 'uuid': 'this is a uuid'},
        {'line_number': 1, 'sentence': 'this is a sentence', 'uuid': 'this is a uuid'},
        {'line_number': 1, 'sentence': 'this is a sentence', 'uuid': 'this is a uuid'}
    ]
    scraper = ALZConnectedScrapingPipeline()
    p = Path.cwd() / 'tests' / 'testing_data' / 'test_save_sentences.jsonl'
    scraper.save_sentences(sentences, p, 'w')

base = Path.cwd() / 'tests' / 'testing_data'
scraper = ALZConnectedScrapingPipeline(
)

ScrapingPipeline.process_sentences(
    ScrapingPipeline.load_scrape_output(base / 'test_scrape.jsonl'),
    base / 'test_sentence.jsonl',
    'w'
)

