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

# DEMENTIA SUPPORT FORUM

DementiaSupportForum_I_HAVE_DEMENTIA = {
    'forum_name': 'dementiasupportforum/i_have_dementia',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/i-have-dementia.56/page-', start=1, stop=109, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_I_HAVE_A_PARTNER_WITH_DEMENTIA = {
    'forum_name': 'dementiasupportforum/i_have_a_partner_with_dementia',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/i-have-a-partner-with-dementia.69/page-', start=1, stop=620, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_I_CARE_FOR_A_PERSON_WITH_DEMENTIA = {
    'forum_name': 'dementiasupportforum/i_care_for_a_person_with_dementia',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/i-care-for-a-person-with-dementia.70/page-', start=1, stop=1471, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_I_CARE_FOR_A_PERSON_WITH_DEMENTIA_AND_CANCER = {
    'forum_name': 'dementiasupportforum/i_care_for_a_person_with_dementia_and_cancer',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/caring-for-a-person-with-dementia-and-cancer.81/page-', start=1, stop=11, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_YOUNGER_PERSON_WITH_DEMENTIA_AND_THEIR_CAREERS = {
    'forum_name': 'dementiasupportforum/younger_person_with_dementia_and_their_careers',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/younger-people-with-dementia-and-their-carers.27/page-', start=1, stop=137, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_LGBTQ_PEOPLE_WITH_DEMENTIA_AND_THEIR_CAREERS = {
    'forum_name': 'dementiasupportforum/lgbtq_people_with_dementia_and_their_careers',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/lgbt-people-with-dementia-and-carers.46/page-', start=1, stop=7, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_MEMORY_CONCERNS_AND_SEEKING_A_DIAGNOSIS = {
    'forum_name': 'dementiasupportforum/memory_concerns_and_seeking_a_diagnosis',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/memory-concerns-and-seeking-a-diagnosis.26/page-', start=1, stop=108, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_RECENTLY_DIAGNOSED_AND_EARLY_STAGES_OF_DIAGNOSIS = {
    'forum_name': 'dementiasupportforum/recently_diagnosed_and_early_stages_of_diagnosis',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/recently-diagnosed-and-early-stages-of-dementia.71/page-', start=1, stop=87, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_MIDDLE_EARLY_STAGES_OF_DEMENTIA = {
    'forum_name': 'dementiasupportforum/middle_late_stages_of_dementia',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/middle-later-stages-of-dementia.72/page-', start=1, stop=238, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_END_OF_LIFE_CARE = {
    'forum_name': 'dementiasupportforum/end_of_life_care',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/end-of-life-care.73/page-', start=1, stop=90, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_AFTER_DEMENTIA_DEALING_WITH_LOSS = {
    'forum_name': 'dementiasupportforum/after_dementia_dealing_with_loss',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/after-dementia-%E2%80%94-dealing-with-loss.28/page-', start=1, stop=126, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_DEMENTIA_RELATED_NEWS_AND_CAMPAIGNS = {
    'forum_name': 'dementiasupportforum/dementia_related_news_and_campaigns',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/dementia-related-news-and-campaigns.34/page-', start=1, stop=160, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_LEGAL_AND_FINANCIAL_ISSUES = {
    'forum_name': 'dementiasupportforum/legal_and_financial_issues',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/legal-and-financial-issues.60/page-', start=1, stop=362, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_HELPFUL_WEBSITES = {
    'forum_name': 'dementiasupportforum/helpful_websites',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/helpful-websites.74/page-', start=1, stop=14, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_HEALTH_AND_WELLBEING = {
    'forum_name': 'dementiasupportforum/health_and_wellbeing',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/health-and-wellbeing.75/page-', start=1, stop=31, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_BOOKS_AND_FILMS = {
    'forum_name': 'dementiasupportforum/books_and_films',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/books-film-and-music.76/page-', start=1, stop=12, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_EQUIPMENT_AND_TECHNOLOGY = {
    'forum_name': 'dementiasupportforum/equipment_and_technology',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/equipment-and-technology.77/page-', start=1, stop=31, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_FUNDRAISING_FOR_ALZHIEMERS_SOCIETY = {
    'forum_name': 'dementiasupportforum/fundraiser_for_alzheimers_society',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/fundraising-for-alzheimers-society.59/page-', start=1, stop=18, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_INNOVATIONS_AND_RESEARCH = {
    'forum_name': 'dementiasupportforum/innovations_and_research',
    'seeds': seed_generator(prefix='https://forum.alzheimers.org.uk/forums/innovation-and-research.35/page-', start=1, stop=47, suffix=''),
    'num_crawlers': NUMBER_OF_CRAWLERS,
    'num_scrapers': NUMBER_OF_SCRAPERS,
    'type_scraping_pipeline': DementiaSupportForumScrapingPipeline
}

DementiaSupportForum_TOTAL = [
    DementiaSupportForum_I_HAVE_DEMENTIA,
    DementiaSupportForum_I_HAVE_A_PARTNER_WITH_DEMENTIA,
    DementiaSupportForum_I_CARE_FOR_A_PERSON_WITH_DEMENTIA,
    DementiaSupportForum_I_CARE_FOR_A_PERSON_WITH_DEMENTIA_AND_CANCER,
    DementiaSupportForum_YOUNGER_PERSON_WITH_DEMENTIA_AND_THEIR_CAREERS,
    DementiaSupportForum_LGBTQ_PEOPLE_WITH_DEMENTIA_AND_THEIR_CAREERS,
    DementiaSupportForum_MEMORY_CONCERNS_AND_SEEKING_A_DIAGNOSIS,
    DementiaSupportForum_RECENTLY_DIAGNOSED_AND_EARLY_STAGES_OF_DIAGNOSIS,
    DementiaSupportForum_MIDDLE_EARLY_STAGES_OF_DEMENTIA,
    DementiaSupportForum_END_OF_LIFE_CARE,
    DementiaSupportForum_AFTER_DEMENTIA_DEALING_WITH_LOSS,
    DementiaSupportForum_DEMENTIA_RELATED_NEWS_AND_CAMPAIGNS,
    DementiaSupportForum_LEGAL_AND_FINANCIAL_ISSUES,
    DementiaSupportForum_HELPFUL_WEBSITES,
    DementiaSupportForum_BOOKS_AND_FILMS,
    DementiaSupportForum_EQUIPMENT_AND_TECHNOLOGY,
    DementiaSupportForum_FUNDRAISING_FOR_ALZHIEMERS_SOCIETY,
    DementiaSupportForum_INNOVATIONS_AND_RESEARCH,

]