from base_classes import TicketManip
from utils import get_user_creds, get_variable, get_user_info, get_ticket_info
from selenium import webdriver
import requests
import re
from requests.exceptions import ConnectionError, Timeout, HTTPError, ConnectTimeout
from requests.packages.urllib3.exceptions import ConnectTimeoutError, MaxRetryError
from socket import timeout
from selenium.common.exceptions import TimeoutException
from os import path
import unittest


class Cure53_06_2017_Audit(TicketManip):

    def setUp(self):
        self.civicdr_url = get_variable("BASE_URL")

    def test_CDR_01_001(self):
        """Tests for the presence of appropriate headers (not full implementation)

        This test should be expanded once the header values have been chosen for the platform.
        See test_CDR_01_003 for an example
        """
        desired_headers = ['X-XSS-Protection',
                           'X-Content-Type-Options',
                           'X-Frame-Options',
                           'Strict-Transport-Security']
        r = requests.get(self.civicdr_url, timeout=5)
        actual_headers = dict(r.headers).keys()
        for i in desired_headers:
            self.assertIn(i,
                          actual_headers,
                          "{0} missing from headers".format(i))

    def test_CDR_01_002(self):
        """Tests for HTTPS
        """
        failed = None
        https_url = None
        if re.match("https://.*", self.civicdr_url):
            https_url = self.civicdr_url
        elif re.match("http://.*", self.civicdr_url):
            https_url = re.sub("http://", "https://", self.civicdr_url)
        else:
            https_url = "https://" + self.civicdr_url
        try:
            r = requests.get(https_url, timeout=5)
        except (ConnectionError, Timeout, HTTPError,
                ConnectTimeout, ConnectTimeoutError,
                MaxRetryError, AssertionError, timeout):
            failed = True
        if failed is not None:
            self.fail("Could not request site over HTTPS")

    def test_CDR_01_003_headers(self):
        """Tests for presence of XXS protection headers
        """
        desired_headers = {'X-Content-Type-Options':'NOSNIFF',
                           'X-Frame-Options':"DENY"}
        r = requests.get(self.civicdr_url, timeout=5)
        for header, value in desired_headers.items():
            cur_val = r.headers.get(header)
            if cur_val is None:
                self.fail("XXS header {0} not in place".format(header))
            else:
                cur_val = cur_val.upper()
            error = "Bad {0} value. Should be {1}. Is {2}".format(header,
                                                                  value,
                                                                  cur_val)
            self.assertEqual(cur_val, value, error)

    def test_CDR_01_003_key(self):
        self.driver = webdriver.Chrome()
        self.addCleanup(self.driver.close)
        driver = self.driver
        self.login("Admin")
        self.recreate_profile("SP")
        self.recreate_profile("IP")
        href = self.get_test_user_href("IP", 0)
        key_path = path.join(href, "key")
        try:
            driver.get(key_path)
            self.wait_for_page("404", "all", 10)
        except TimeoutException:
            self.fail("PGP route still exists for IP users")
        href = self.get_test_user_href("SP", 0)
        key_path = path.join(href, "key")
        try:
            driver.get(key_path)
            self.wait_for_page("404", "all", 10)
        except TimeoutException:
            self.fail("PGP route still exists for SP users")

    def test_CDR_01_004(self):
        if re.search("www.civicdr.org.s3", self.civicdr_url):
            self.fail("If using an S3 bucket. Name should not include periods.")

    def test_CDR_01_005(self):
        self.driver = webdriver.Chrome()
        self.addCleanup(self.driver.close)
        self.login("Admin")
        logout_csrf = path.join(self.civicdr_url, "#access_token=a&token_type=Bearer")
        driver = self.driver
        driver.implicitly_wait(10)
        driver.get(logout_csrf)
        driver.get(self.civicdr_url)
        try:
            self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, 10)
        except TimeoutException:
            self.fail("CSRF protection is not in place")

    def test_CDR_01_006_Ratings(self):
        raise NotImplementedError("Not yet Implemented")


    def test_CDR_01_006_OpenID_reset(self):
        raise NotImplementedError("Not yet Implemented")


    def test_CDR_01_007(self):
        raise NotImplementedError("Not yet Implemented")
        self.driver = webdriver.Chrome()
        self.addCleanup(self.driver.close)
        self.recreate_profile("IP")
        # TODO Try to create multiples of IP using same data
        # TODO Check how many exist
        # TODO If more than one, fail
        self.recreate_profile("SP")
        # TODO Try to create multiples of SP using same data
        # TODO Check how many exist
        # TODO If more than one, fail

if __name__ == '__main__':
    unittest.main()
