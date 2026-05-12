from thematic_analysis_model.model.scraping_pipeline import *
from thematic_analysis_model.model.util import *
import pytest
import pathlib

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

# test save seeds
def test_save_and_read_seeds():
    seeds = [
        'www.testWebsite/p1/testing.com',
        'www.testWebsite/p2/testing.com',
        'www.testWebsite/p3/testing.com',
        'www.testWebsite/p4/testing.com',
        'www.testWebsite/p5/testing.com',
    ]
    seeds_shortened = [
        'www.testWebsite/p1/testing.com',
        'www.testWebsite/p2/testing.com',
        'www.testWebsite/p3/testing.com'
    ]

    location = pathlib.Path.cwd() / 'tests' / 'testing_data' / 'test_seeds.txt'

    save_seeds(location, seeds)
    output = read_seeds(location)

    assert seeds == output

# test method for requesting page from html
# scraping from https://www.scrapethissite.com/pages/ (Tue May 12 2026, 10:30AM)
# if tests starts failing, website might have changed
def test_request_page():
    link = 'https://www.scrapethissite.com/pages/'
    page_html = request_page(link)
    test_path = pathlib.Path.cwd() / 'tests' / 'testing_data' / 'testing_request_page.txt'
    expected_html = smart_load(test_path)   

    assert page_html == expected_html

# testing ALZConnected.org crawler, using https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p10 as the seed
# note test written Monday 11th, May 2026 11:30 AM, so links may change. Keep this in mind if tests start to fail.
def test_ALZConnected_crawler():
    seed = ['https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p10']
    p = pathlib.Path.cwd() / 'tests' / 'testing_data' / 'test_crawl_output.txt'

    pipeline = ALZConnectedScrapingPipeline(seeds=seed, crawl_save_location=p)   

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

    assert pipeline.crawl_output == expected_set





