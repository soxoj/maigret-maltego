import asyncio
import logging
from mock import Mock

from maltego_trx.entities import Alias, URL

from maltego_trx.transform import DiscoverableTransform
from maltego_trx.maltego import LINK_STYLE_DASHED

from maigret.maigret import maigret
from maigret.result import QueryStatus
from maigret.sites import MaigretDatabase

MAIGRET_DB_URL = 'https://raw.githubusercontent.com/soxoj/maigret/main/maigret/resources/data.json'
DB = MaigretDatabase().load_from_url(MAIGRET_DB_URL)
TOP_SITES_COUNT = 500
TIMEOUT = 5


PROPERTIES = {
    'SocialNetwork': {
        'label': 'Social Network',
    },
    'URL': {
        'label': 'URL',
    }
}


async def maigret_search(username):
    """
        Main Maigret search function
    """
    global DB

    log_level = logging.WARNING
    logging.basicConfig(
        format='[%(filename)s:%(lineno)d] %(levelname)-3s  %(asctime)s %(message)s',
        datefmt='%H:%M:%S',
        level=log_level
    )
    logger = logging.getLogger('maigret')
    logger.setLevel(log_level)

    # workaround to update database from git master
    try:
        db = MaigretDatabase().load_from_url(MAIGRET_DB_URL)
        DB = db
    except Exception as e:
        logger.error(e)
        db = DB

    site_data = db.ranked_sites_dict(top=TOP_SITES_COUNT)
    # can be object with editing tg msg handler to show search progress
    query_notify = Mock()

    results = await maigret(username,
                            dict(site_data),
                            query_notify,
                            timeout=TIMEOUT,
                            logger=logger,
                            no_progressbar=True,
                            recursive_search=True,
                            )
    return results


class Maigret(DiscoverableTransform):
    """
    Returns aliases for .
    """

    @classmethod
    def create_entities(cls, request, response):
        person_name = request.Value

        for site, data in Maigret.get_maigret_data(person_name).items():
            url_main = data['url_main']

            entity = response.addEntity(URL, url_main)
            entity.setLinkLabel('found by username')
            entity.addDisplayInformation(content='hello')
            # entity.setWeight(100)
            entity.setIconURL('https://www.google.com/s2/favicons?domain='+url_main)
            for key in ['url', 'Social Network', 'Title']:
                entity.addProperty(key.replace(' ', ''), key, 'strict', url_main)

    @staticmethod
    def get_maigret_data(username):
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(maigret_search(username))

        res = {}
        for site, data in results.items():
            if data['status'].status == QueryStatus.CLAIMED:
                res[site] = data

        return res


if __name__ == '__main__':
    print(Maigret().get_maigret_data('soxoj'))
