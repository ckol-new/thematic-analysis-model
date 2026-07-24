# configs for scraping
from .scraping import ScrapingPipeline, dementiasupportforumScrapingPipeline, alzconnectedScrapingPipeline

from pydantic import BaseModel

# class
class scrape_config(BaseModel):
    forum_origin: str
    seeds: list[str]
    type_scraping_pipeline: type

# Alzhemier Connected Forum
alzconnected_i_am_living_with_dementia_or_other = scrape_config(
    forum_origin='alzconnected/i_am_living_with_dementia_or_other',
    seeds=ScrapingPipeline.seed_generator(prefix="https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p", start=1, stop=13, suffix=''),
    type_scraping_pipeline=alzconnectedScrapingPipeline
)
alzconnected_i_am_living_with_younger_onset_dementia = scrape_config(
    forum_origin='alzconnected/i_am_living_with_youger_onset_dementia',
    seeds=ScrapingPipeline.seed_generator(prefix="https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p", start=1, stop=10, suffix=''),
    type_scraping_pipeline=alzconnectedScrapingPipeline
)
alzconnected_i_am_a_caregiver_general_topics = scrape_config(
    forum_origin='alzconnected/i_am_a_caregiver_general_topics',
    seeds=ScrapingPipeline.seed_generator(prefix="https://alzconnected.org/categories/i-am-a-caregiver-%28general-topics%29/p", start=1, stop=194, suffix=''),
    type_scraping_pipeline=alzconnectedScrapingPipeline
)
alzconnected_caring_for_spouse_or_partner= scrape_config(
    forum_origin='alzconnected/caring_for_spouse_or_partner',
    seeds=ScrapingPipeline.seed_generator(prefix="https://alzconnected.org/categories/spouses-or-partners/p", start=1, stop=302, suffix=''),
    type_scraping_pipeline=alzconnectedScrapingPipeline
)
alzconnected_caring_for_a_parent = scrape_config(
    forum_origin='alzconnected/caring_for_a_parent',
    seeds=ScrapingPipeline.seed_generator(prefix="https://alzconnected.org/categories/caring-for-a-parent/p", start=1, stop=108, suffix=''),
    type_scraping_pipeline=alzconnectedScrapingPipeline
)
alzconnected_caring_long_distance = scrape_config(
    forum_origin='alzconnected/caring_long_distance',
    seeds=ScrapingPipeline.seed_generator(prefix="https://alzconnected.org/categories/caring-long-distance/p", start=1, stop=9, suffix=''),
    type_scraping_pipeline=alzconnectedScrapingPipeline
)
alzconnected_supporting_those_who_lost_someone= scrape_config(
    forum_origin='alzconnected/supporting_those_who_lost_someone',
    seeds=ScrapingPipeline.seed_generator(prefix="https://alzconnected.org/categories/supporting-those-who-have-lost-someone/p", start=1, stop=7, suffix=''),
    type_scraping_pipeline=alzconnectedScrapingPipeline
)
alzconnected_ALL = [
    alzconnected_i_am_living_with_dementia_or_other,
    alzconnected_i_am_living_with_younger_onset_dementia,
    alzconnected_i_am_a_caregiver_general_topics,
    alzconnected_caring_for_spouse_or_partner,
    alzconnected_caring_for_a_parent,
    alzconnected_caring_long_distance,
    alzconnected_supporting_those_who_lost_someone
]

# dementia support forum
dementiasupportforum_i_have_dementia = scrape_config(
    forum_origin='dementiasupportforum/i_have_dementia',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/i-have-dementia.56/page-', start=1, stop=109, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_i_have_a_partner_with_dementia = scrape_config(
    forum_origin='dementiasupportforum/i_have_a_partner_with_dementia',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/i-have-a-partner-with-dementia.69/page-', start=1, stop=622, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_i_care_for_a_person_with_dementia = scrape_config(
    forum_origin='dementiasupportforum/i_care_for_a_person_with_dementia',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/i-care-for-a-person-with-dementia.70/page-', start=1, stop=1472, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_i_care_for_a_person_with_dementia_and_cancer = scrape_config(
    forum_origin='dementiasupportforum/i_care_for_a_person_with_dementia_and_cancer',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/caring-for-a-person-with-dementia-and-cancer.81/page-', start=1, stop=11, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_younger_people_dementia_and_their_careers= scrape_config(
    forum_origin='dementiasupportforum/younger_people_dementia_and_their_careers',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/younger-people-with-dementia-and-their-carers.27/page-', start=1, stop=137, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_lgbtq_people_with_dementia_and_their_careers = scrape_config(
    forum_origin='dementiasupportforum/lgbtq_people_with_dementia_and_their_careers',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/lgbt-people-with-dementia-and-carers.46/page-', start=1, stop=7, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_memory_concerns_and_seeking_a_diagnosis = scrape_config(
    forum_origin='dementiasupportforum/memory_concerns_and_seeking_a_diagnosis',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/memory-concerns-and-seeking-a-diagnosis.26/page-', start=1, stop=108, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_recently_diagnosed_and_early_stages_of_dementia = scrape_config(
    forum_origin='dementiasupportforum/recently_diagnosed_and_early_stages_of_dementia',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/recently-diagnosed-and-early-stages-of-dementia.71/page-', start=1, stop=87, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_middle_later_stages_of_dementia = scrape_config(
    forum_origin='dementiasupportforum/middle_later_stages_of_dementia',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/middle-later-stages-of-dementia.72/page-', start=1, stop=238, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_end_of_life_care = scrape_config(
    forum_origin='dementiasupportforum/end_of_life_care',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/end-of-life-care.73/page-', start=1, stop=90, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_after_dementia_dealing_with_loss = scrape_config(
    forum_origin='dementiasupportforum/after_dementia_dealing_with_loss',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/after-dementia-%E2%80%94-dealing-with-loss.28/page-', start=1, stop=125, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)

dementiasupportforum_dementia_related_news_and_campaigns = scrape_config(
    forum_origin='dementiasupportforum/dementia_related_news_and_campaigns',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/dementia-related-news-and-campaigns.34/page-', start=1, stop=160, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_legal_and_financial_issues = scrape_config(
    forum_origin='dementiasupportforum/legal_and_financial_issues',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/legal-and-financial-issues.60/page-', start=1, stop=362, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_helpful_websites = scrape_config(
    forum_origin='dementiasupportforum/helpful_websites',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/helpful-websites.74/page-', start=1, stop=14, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_books_film_and_music = scrape_config(
    forum_origin='dementiasupportforum/books_film_and_music',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/books-film-and-music.76/page-', start=1, stop=12, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_equipment_and_technology = scrape_config(
    forum_origin='dementiasupportforum/equipment_and_technology',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/equipment-and-technology.77/page-', start=1, stop=31, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_fundraising_for_alzheimers_society = scrape_config(
    forum_origin='dementiasupportforum/fundraising_for_alzheimers_society',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/fundraising-for-alzheimers-society.59/page-', start=1, stop=18, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_innovation_and_research = scrape_config(
    forum_origin='dementiasupportforum/innovation_and_research',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/innovation-and-research.35/page-', start=1, stop=47, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)
dementiasupportforum_archive_forum_support_discussion = scrape_config(
    forum_origin='dementiasupportforum/archive_forum_support_discussion',
    seeds=ScrapingPipeline.seed_generator(prefix='https://forum.alzheimers.org.uk/forums/archive-forum-support-discussions.25/page-', start=1, stop=1543, suffix=''),
    type_scraping_pipeline=dementiasupportforumScrapingPipeline
)

dementiasupportforum_ALL = [
    dementiasupportforum_i_have_dementia,
    dementiasupportforum_i_have_a_partner_with_dementia,
    dementiasupportforum_i_care_for_a_person_with_dementia,
    dementiasupportforum_i_care_for_a_person_with_dementia_and_cancer,
    dementiasupportforum_younger_people_dementia_and_their_careers,
    dementiasupportforum_lgbtq_people_with_dementia_and_their_careers,
    dementiasupportforum_memory_concerns_and_seeking_a_diagnosis,
    dementiasupportforum_recently_diagnosed_and_early_stages_of_dementia,
    dementiasupportforum_middle_later_stages_of_dementia,
    dementiasupportforum_end_of_life_care,
    dementiasupportforum_after_dementia_dealing_with_loss,
    dementiasupportforum_dementia_related_news_and_campaigns,
    dementiasupportforum_legal_and_financial_issues,
    dementiasupportforum_helpful_websites,
    dementiasupportforum_books_film_and_music,
    dementiasupportforum_equipment_and_technology,
    dementiasupportforum_innovation_and_research,
    dementiasupportforum_fundraising_for_alzheimers_society,
    dementiasupportforum_archive_forum_support_discussion
]