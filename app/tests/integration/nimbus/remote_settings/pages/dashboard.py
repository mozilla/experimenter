from pypom import Page, Region
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Dashboard(Page):

    _bucket_menu_locator = (By.CSS_SELECTOR, ".bucket-menu")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._bucket_menu_locator))
        return self

    def __init__(self, selenium, base_url, **kwargs):
        super(Dashboard, self).__init__(selenium, base_url, timeout=60, **kwargs)

    @property
    def buckets(self):
        els = self.find_elements(*self._bucket_menu_locator)
        return [self.BucketCard(self, el) for el in els]

    @property
    def record(self):
        _root_locator = (By.CSS_SELECTOR, ".list-actions")
        self.wait.until(EC.presence_of_element_located(_root_locator))
        self.find_element(*_root_locator)
        return self.Record(self)

    class BucketCard(Region):

        _page_wait_locator = (By.CSS_SELECTOR, ".main")

        _card_header_name_locator = (By.CSS_SELECTOR, ".card-header > strong")
        _bucket_category_locator = (By.CSS_SELECTOR, ".list-group .list-group-item a")

        def wait_for_page_to_load(self):
            self.wait.until(EC.presence_of_element_located(self._page_wait_locator))
            return self

        @property
        def bucket_name(self):
            return self.find_element(*self._card_header_name_locator)

        @property
        def bucket_category(self):
            return self.find_elements(*self._bucket_category_locator)

    class Record(Region):

        _approve_locator = (By.CSS_SELECTOR, ".list-page .interactive .btn-success")
        _reject_locator = (By.CSS_SELECTOR, ".interactive .btn-danger")

        @property
        def id(self):
            els = self.find_elements(By.CSS_SELECTOR, ".table td")
            return els[0].text

        def approve(self):
            def _wait_for_it(selenium):
                try:
                    selenium.find_element(*self._approve_locator)
                except NoSuchElementException:
                    selenium.refresh()
                    return False
                else:
                    return True

            self.wait.until(_wait_for_it)
            el = self.find_element(*self._approve_locator)
            el.click()
