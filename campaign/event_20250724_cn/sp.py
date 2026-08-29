class Campaign(CampaignBase):

    @staticmethod
    def _campaign_ocr_result_process(result):
        result = CampaignBase._campaign_ocr_result_process(result)
        if result in ['ysp', 'usp', 'iisp', 'ijsp', 'jjsp']:
            result = 'sp'
        return result
