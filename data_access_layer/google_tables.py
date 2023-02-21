import pygsheets


class SheetsClient:

    def __init__(self, table_key):
        self.client = pygsheets.authorize(service_file='data_access_layer/account_credentials.json')
        self.sheet = self.client.open_by_key(table_key)
        self.words_list_sheet = self.sheet.worksheet_by_title('База исследований')

    def insert_word_pair(self, word, meaning):
        self.words_list_sheet.insert_rows(1, 1, [word, meaning])



    def insert_field_research(self,
                              weekday,
                              time,
                              number,
                              location,
                              is_order_taken_by_courier,
                              guests_count,
                              drinks_count,
                              desserts_count,
                              dishes_count,
                              order_type,
                              order_amount):
        self.words_list_sheet.insert_rows(1, 1, [weekday,
                                                 time,
                                                 number,
                                                 location,
                                                 is_order_taken_by_courier,
                                                 guests_count,
                                                 drinks_count,
                                                 desserts_count,
                                                 dishes_count,
                                                 order_type,
                                                 order_amount])
