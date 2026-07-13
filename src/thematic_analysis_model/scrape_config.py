from .model.util import seed_generator
from .config import NUMBER_OF_CRAWLERS, NUMBER_OF_SCRAPERS
from .model.scraping import ALZConnectedScrapingPipeline, DementiaSupportForumScrapingPipeline

# ALZ Connected
ALZConnected_EARLY_ONSET = {
    'forum_name': 'alzconnected/I_am_living_with_younger_onset_dementia',
    'seeds': seed_generator(prefix='https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p', start=1, stop=10, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': ALZConnectedScrapingPipeline
}
ALZConnected_DEMENTIA_OR_OTHER = {
    'forum_name': 'alzconnected/I_am_living_with_alzheimers_or_other_dementia',
    'seeds': seed_generator(prefix='https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p', start=1, stop=13, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': ALZConnectedScrapingPipeline
}
ALZConnected_CAREGIVER_GENERAL = {
    'forum_name': 'alzconnected/I_am_a_caregiver_general_topics',
    'seeds': seed_generator(prefix='https://alzconnected.org/categories/i-am-a-caregiver-%28general-topics%29/p', start=1, stop=194, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': ALZConnectedScrapingPipeline
}
ALZConnected_CARING_FOR_SPOUSE_OR_PARTNER = {
    'forum_name': 'alzconnected/caring_for_spouse_or_partner',
    'seeds': seed_generator(prefix='https://alzconnected.org/categories/spouses-or-partners/p', start=1, stop=300, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': ALZConnectedScrapingPipeline
}
ALZConnected_CARING_FOR_PARENT = {
    'forum_name': 'alzconnected/caring_for_parent',
    'seeds': seed_generator(prefix='https://alzconnected.org/categories/caring-for-a-parent/p', start=1, stop=107, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': ALZConnectedScrapingPipeline
}
ALZConnected_CARING_LONGDISTANCE = {
    'forum_name': 'alzconnected/caring_long_distance',
    'seeds': seed_generator(prefix='https://alzconnected.org/categories/caring-long-distance/p', start=1, stop=9, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': ALZConnectedScrapingPipeline
}
ALZConnected_CARING_FOR_THOSE_WHO_LOST_SOMEONE = {
    'forum_name': 'alzconnected/caring_for_those_who_lost_someone',
    'seeds': seed_generator(prefix='https://alzconnected.org/categories/supporting-those-who-have-lost-someone/p', start=1, stop=7, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': ALZConnectedScrapingPipeline
}

ALZConnected_total = [
    ALZConnected_EARLY_ONSET, ALZConnected_DEMENTIA_OR_OTHER, ALZConnected_CAREGIVER_GENERAL, ALZConnected_CARING_FOR_SPOUSE_OR_PARTNER, ALZConnected_CARING_FOR_PARENT, ALZConnected_CARING_LONGDISTANCE, ALZConnected_CARING_FOR_THOSE_WHO_LOST_SOMEONE
]

