#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of CiviCDR functionality tests, a set of functionality tests for the CiviCDR website.
# Copyright © 2017 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

from base_classes import ProfileTest, NewProfile, TicketManip

import unittest
from utils import get_user_creds, get_variable, get_user_info, get_ticket_info
from selenium import webdriver
from selenium.common.exceptions import TimeoutException


class NewSP(NewProfile):

    BASE_USER_TYPE = "SP"
    PROFILE_LOCATION = "#/service-providers/new"
    PROFILE_REQUIRED = ["Name",
                        "Primary E-mail",
                        "Description",
                        "Fees"]
                        # "Start Time", # Auto-filled
                        # "Availability", # Auto-filled


class NewIP(NewProfile):

    BASE_USER_TYPE = "IP"
    PROFILE_LOCATION = "#/partners/new"
    PROFILE_REQUIRED = ["Name",
                        "Primary E-mail",
                        "Would you like to receive email notifications for changes to ticket statuses or assignments?"]


class AdminLogin(ProfileTest):

    BASE_USER_TYPE = "Admin"

    def setUp(self):
        self.civicdr_url = get_variable("BASE_URL")
        self.driver = webdriver.Chrome()
        self.addCleanup(self.driver.close)

    def test_ticket_list_on_login(self):
        """Test that an admin will be taken to the ticket list on login
        """
        driver = self.driver
        driver.get(self.civicdr_url)
        # Wait for next page to load
        try:
            self.login(self.BASE_USER_TYPE, user_num=0)
            self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, 10)
        except TimeoutException:
            self.fail("Admin did not successfully login")


class TicketTests(TicketManip):

    BASE_USER_TYPE = "Admin"

    def test_create_ticket(self):
        """Tests that a user can create a ticket
        """
        self.recreate_ip_profile()
        created_ticket = self.create_ticket()
        self.assertIsNotNone(created_ticket)

    def test_IP_deleteable_with_ticket(self):
        """Create and delete an IP profile after it has created a ticket
        """
        driver = self.driver
        created_ticket = self.setup_ticket_scenerio()
        self.login("IP", user_num=0)
        self.wait_for_page("ticket tracking", delay=10)
        self.delete_profile("IP", delete_tickets=False)
        self.wait_for_page("login", "Admin", 10)
        try:
            self.login("IP", user_num=0, wait_page="new profile")
        except TimeoutException:
            self.fail("IP was not successfully deleted.")
        self.create_profile("IP")
        self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, 10)
        all_tickets = driver.find_elements_by_css_selector('article[class="card"]')
        num_tickets = len(all_tickets)
        self.assertEqual(0, num_tickets, "Deleting user did not delete their tickets")
        # Clean up
        self.delete_profile("IP", delete_tickets=False)

    def test_sp_assigned_to_ticket(self):
        """Test that an SP can be assigned to a ticket.
        """
        driver = self.driver
        created_ticket = self.setup_ticket_scenerio()
        try:
            self.create_profile("SP")
        except TimeoutException:
            pass
        self.login("Admin", user_num=0)
        driver.get(created_ticket)
        self.wait_for_page("ticket view", delay=10)
        self.assign_sp_to_ticket()
        self.login("SP")
        # print(created_ticket)
        driver.get(created_ticket)
        try:
            self.wait_for_page("ticket view", delay=10)
        except TimeoutException:
            self.fail("SP not able to access ticket")

    def test_sp_filter_by_start_time(self):
        """Test that an admin can filter the SP list by SP start time.
        """
        raise NotImplementedError("NOT YET IMPLEMENTED")

    def test_sp_filter_by_availability(self):
        """Test that an admin can filter the SP list by SP availability
        """
        raise NotImplementedError("NOT YET IMPLEMENTED")

    def test_sp_filter_by_services(self):
        """Test that an admin can filter the SP list by services SP's provide
        """
        raise NotImplementedError("NOT YET IMPLEMENTED")

    def test_assign_grouping_to_ticket(self):
        """Test that an admin can assign a grouping to a ticket
        """
        raise NotImplementedError("NOT YET IMPLEMENTED")

    def test_create_grouping(self):
        """Test that an admin can create a grouping
        """
        raise NotImplementedError("NOT YET IMPLEMENTED")

    def test_SP_deleteable_when_assigned_to_ticket(self):
        """Create and delete an SP profile after it is assigned to a ticket
        """
        raise NotImplementedError("NOT YET IMPLEMENTED")
        self.setup_ticket_scenerio()
        self.create_profile("SP")
        self.wait_for_page("ticket tracking", delay=10)

        self.delete_profile(self.BASE_USER_TYPE)
        self.login(self.BASE_USER_TYPE, user_num=0)

    def test_switch_SP_assigned_to_ticket(self):
        """Create and delete an SP profile after it is assigned to a ticket
        """
        # First SP no longer has access
        # Second SP has access
        # SP data removed from ticket
        # IP is notified
        raise NotImplementedError("NOT YET IMPLEMENTED")

if __name__ == '__main__':
    unittest.main()
