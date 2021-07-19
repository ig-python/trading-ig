from trading_ig.rest import IGService, ApiExceededException
from trading_ig.config import config
from tenacity import Retrying, wait_exponential, retry_if_exception_type

DEFAULT_RETRY = Retrying(wait=wait_exponential(),
        retry=retry_if_exception_type(ApiExceededException))


def display_top_level_nodes():
    ig_service = get_session()

    response = ig_service.fetch_top_level_navigation_nodes()
    df = response['nodes']
    for record in df.to_dict('records'):
        print(f"{record['name']} [{record['id']}]")


def display_all_epics():
    ig_service = get_session()
    response = ig_service.fetch_top_level_navigation_nodes()
    df = response['nodes']
    for record in df.to_dict('records'):
        print(f"{record['name']} [{record['id']}]")
        display_epics_for_node(record['id'], space='  ', ig_service=ig_service)


def display_epics_for_node(node_id=0, space='', ig_service=None):
    if ig_service is None:
        ig_service = get_session()

    sub_nodes = ig_service.fetch_sub_nodes_by_node(node_id)

    if sub_nodes['nodes'].shape[0] != 0:
        rows = sub_nodes['nodes'].to_dict('records')
        for record in rows:
            print(f"{space}{record['name']} [{record['id']}]")
            display_epics_for_node(record['id'], space=space + '  ', ig_service=ig_service)

    if sub_nodes['markets'].shape[0] != 0:
        cols = sub_nodes['markets'].to_dict('records')
        for record in cols:
            print(f"{space}{record['instrumentName']} ({record['expiry']}): {record['epic']}")


def get_session():
    ig_service = IGService(
        config.username,
        config.password,
        config.api_key,
        config.acc_type,
        acc_number=config.acc_number,
        retryer=DEFAULT_RETRY)
    ig_service.create_session(version='3')
    return ig_service

if __name__ == "__main__":

    display_top_level_nodes()
    #display_all_epics()

    """
    Weekend Markets [191926749]
    Indices [97601]
    Forex [195235]
    Commodities Metals Energies [101515]
    Cryptocurrency [668394]
    Bonds and Moneymarket [108092]
    ETFs, ETCs & Trackers [184730]
    Shares - UK [180500]
    Shares - UK International (IOB) [97695]
    Shares - US (All Sessions) [298158]
    Shares - US [97477]
    Shares - Austria [114058]
    Shares - Belgium [114036]
    Shares - Canada [103185]
    Shares - Denmark [419769]
    Shares - Finland [99514]
    Shares - France [113659]
    Shares - LSE (UK) [172904]
    Shares - Germany [97466]
    Shares - Greece [100437]
    Shares - Hong Kong [105775]
    Shares - Ireland (LSE) [421257]
    Shares - Ireland (Euronext Dublin) [99578822]
    Shares - Netherlands [105509]
    Shares - New Zealand [127489792]
    Shares - Norway [99808]
    Shares - Portugal [99787]
    Shares - Singapore [105781]
    Shares - South Africa [100066]
    Shares - Sweden [113681]
    Shares - Switzerland [99814]
    IPOs [324080]
    Options (Australia 200) [77976799]
    Options (Eu Stocks 50) [245938]
    Options (France 40) [188760]
    Options (FTSE) [122250]
    Options (Germany) [97612]
    Options (HS 50) [92462573]
    Options (Japan 225) [111915265]
    Options (Netherlands 25) [236490]
    Options (Sweden 30) [319963]
    Options (Taiwan Index) [157168018]
    Options (US 500) [267039]
    Options (US Tech 100) [89291253]
    Options (Wall St) [122505]
    Options on FX Majors [255072]
    Options (Volatility Index) [56719751]
    Options on Metals, Energies [195913]
    """

    #display_epics_for_node(195913)
