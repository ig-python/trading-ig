from tenacity import Retrying, retry_if_exception_type, wait_exponential

from trading_ig.config import config
from trading_ig.rest import ApiExceededException, IGService

DEFAULT_RETRY = Retrying(
    wait=wait_exponential(), retry=retry_if_exception_type(ApiExceededException)
)


def display_categories():
    ig_service = get_session()

    response = ig_service.fetch_categories()
    df = response["categories"]
    for row in df.itertuples(index=False):
        print(f"{row.code}, nonTradeable={row.nonTradeable}")


def display_all_epics():
    ig_service = get_session()
    response = ig_service.fetch_categories()
    df = response["categories"]
    for row in df.itertuples(index=False):
        print(f"{row.code}, nonTradeable={row.nonTradeable}")
        display_epics_for_category(row.code, space="  ", ig_service=ig_service)


def display_epics_for_category(category: str, space="", ig_service=None):
    if ig_service is None:
        ig_service = get_session()

    response = ig_service.fetch_category_instruments(category)
    for row in response["instruments"].itertuples(index=False):
        print(f"{space}{row.instrumentName} ({row.expiry.strip()}): {row.epic}")


def get_session():
    ig_service = IGService(
        config.username,
        config.password,
        config.api_key,
        config.acc_type,
        acc_number=config.acc_number,
        retryer=DEFAULT_RETRY,
    )
    ig_service.create_session(version="3")
    return ig_service


if __name__ == "__main__":
    display_categories()
    # display_all_epics()

    """
    INDICES
    FX
    CRYPTOCURRENCY
    EQUITIES
    COMMODITIES
    BONDS_RATES
    ETF
    OPTIONS
    IPOS
    """

    # display_epics_for_category("INDICES")
