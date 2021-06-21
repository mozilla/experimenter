from pypom import Page, Region
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Dashboard(Page):

    _bucket_menu_locator = (By.CSS_SELECTOR, ".bucket-menu")
    _modal_locator = (By.CSS_SELECTOR, ".modal-content")

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

    @property
    def reject_modal(self):
        el = self.find_element(*self._modal_locator)
        return self.Modal(self, el)

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
        _reject_locator = (By.CSS_SELECTOR, ".list-page  .interactive .btn-danger")

        @property
        def id(self):
            els = self.find_elements(By.CSS_SELECTOR, ".table td")
            return els[0].text

        def action(self, action="approve"):
            def _wait_for_it(selenium):
                try:
                    selenium.find_element(*self._approve_locator)
                except NoSuchElementException:
                    selenium.refresh()
                    return False
                else:
                    return True

            self.wait.until(_wait_for_it)
            if "approve" in action:
                el = self.find_element(*self._approve_locator)
            elif "reject" in action:
                el = self.find_element(*self._reject_locator)
            el.click()

    class Modal(Region):
        _decline_changes_locator = (By.CSS_SELECTOR, ".modal-dialog .btn-primary")

        def decline_changes(self):
            # time.sleep(5)
            # click = self.selenium.execute_script("""
            #     document.querySelector('div.modal-content div.modal-footer button.btn.primary').click();
            # """)
            self.selenium.execute_script(
                """
                document.activeElement.blur()
                document.querySelector('.modal-dialog .btn-primary').click()
                return
            """
            )
            #  self.wait.until(EC.visibility_of_element_located(By.CSS_SELECTOR, "modal-dialog"))
            # _modal_locator = (By.CSS_SELECTOR, ".modal-dialog")
            # el = self.selenium.find_element(*_modal_locator)
            # el.find_element(*self._decline_changes_locator).click()
