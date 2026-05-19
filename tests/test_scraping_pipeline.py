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


