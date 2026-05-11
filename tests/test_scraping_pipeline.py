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

    location = pathlib.Path.cwd() / 'testing_data' / 'test_seeds.txt'

    save_seeds(location, seeds)
    output = read_seeds(location)

    assert seeds == output
