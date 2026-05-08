from thematic_analysis_model.model.scraping_pipeline import *
import pytest

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

    location = r'C:\Users\wslam\Everything\health_city_lab\dfta\thematic-analysis-model\tests\testing_data\test_seeds.txt'

    save_seeds(seeds, location)

    output = read_seeds(location)
    output_shortened = read_seeds(location, 3)

    assert seeds == output
    assert seeds_shortened == output_shortened


test_save_and_read_seeds()


    