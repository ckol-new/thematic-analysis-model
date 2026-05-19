from thematic_analysis_model.model.scraping_pipeline import *

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