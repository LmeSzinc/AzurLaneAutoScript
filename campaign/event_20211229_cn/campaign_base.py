from module.campaign.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'A1 > A2 > A3',
        'B1 > B2 > BS1 > B3',
        'C1 > C2 > C3',
        'D1 > D2 > DS1 > D3',
        'SP1 > SP2 > SP3 > SP4',
        'T1 > T2 > T3 > T4',
    ]
