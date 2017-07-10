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

import unittest
import sys
from os import path
from utils import get_user_creds, get_variable, get_user_info, get_ticket_info, get_usernames
from uuid import uuid4
from datetime import datetime
import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.action_chains import ActionChains


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.civicdr_url = get_variable("BASE_URL")
        self.driver = webdriver.Chrome()
        self.addCleanup(self.driver.close)

    def wait_for_page(self, condition, user_type='all', delay=5):
        """ Have the driver wait until a precondition is met.

        Args:
            condition: The name of a condition to wait for.
            user_type: A user type to use for user type specific conditions
            delay: The number of seconds to wait until throwing an error

        Raises:
            TimeoutException: If the  condition is not met  in the [delay] number of seconds
        """
        driver = self.driver
        # Generic completions
        conditions = {
            "ticket tracking": EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'inpage__headline'),
                "CiviCDR Ticket Tracking"),
            "404": EC.text_to_be_present_in_element(
                (By.CLASS_NAME, "section__title"),
                "404"),
            "login": EC.presence_of_element_located(
                (By.ID, 'auth0-lock-container-1')),
            "create ticket": EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'heading--small'), "Create Ticket"),
            "profile":EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'inpage__stats-item'),
                "Assigned Tickets"),
            "ticket view": EC.presence_of_element_located(
                (By.CLASS_NAME, 'ticket__title')),
                # TODO: give uniquely identifying ID's to different modals
            "sp ticket filter modal gone": EC.invisibility_of_element_located(
                (By.XPATH, '//*[@id="app-container"]/div/main/div/div/div[2]/div[1]/section/div/div/div[1]/h2')),
            "sp ticket filter modal": EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="app-container"]/div/main/div/div/div[2]/div[1]/section/div/div/div[1]/h2')),
                "sp assigned to ticket": EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="app-container"]/div/main/div/div/section/section/ul/li[3]/a')),

            }
        # User specific completions
        user_specific = {
            "IP":{
                "new profile": EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'heading--small'), "Create Partner Profile")
            },
            "SP":{
                "new profile": EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'heading--small'), "Create Provider Profile")
            },
            "Admin":{
                "IP list": EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'inpage__headline'),
                "Implementing Partners"),
                "SP list": EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'inpage__headline'),
                "Service Providers"),
                "ticket delete modal": EC.visibility_of_element_located(
                (By.XPATH,
                     '//*[@id="app-container"]/div/main/section/section/div/div/div/div[1]/div[1]/section/div/div/h2')),
                "user delete modal": EC.visibility_of_element_located(
                (By.XPATH,
                     '//*[@id="app-container"]/div/main/section/div[2]/section/div/div')),
            }
        }
        for key, val in user_specific.get(user_type, {}).items():
            conditions.setdefault(key, val)
        wait = WebDriverWait(driver, delay)
        wait.until(conditions[condition])

    def get_page_targets(self, page, target=None):
        """Get a specific condition based upon the current page and target on that page

        # TODO: Start moving all target identification over to this function
        Args:
            page: The page the target is for
            target: The name of the target
        """
        # Lowercase all requests
        page = page.lower()
        # print(page)
        # Translate acronyms
        if page == "sp":
            page = "service-providers-single"
        elif page == "sps":
            page = "service-providers"
        elif page == "ip":
            page = "partner-single"
        elif page == "ips":
            page = "partners"
        # print(page)
        if target is not None:
            target = target.lower()
        # Page names from https://github.com/ASL-19/civicdr/tree/master/app/assets/scripts/views
        pages = {
            "app":{},
            "auth-callback":{},
            "groupings-single":{},
            "groupings": {},
            "login": {},
            "logout": {},
            "partner-form": {},
            "partner-single": {},
            "partners": {"new":(By.CSS_SELECTOR,'a[href="#/partners/new"]'),
                             "card":(By.CLASS_NAME, 'service-provider-card')}, #sigh
            "provider-form": {},
            "service-providers-single": {},
            "service-providers": {"new":(By.CSS_SELECTOR, 'a[href="#/service-providers/new"]'),
                                  "card":(By.CLASS_NAME, 'service-provider-card')},
            "tickets-form": {},
            "tickets-single": {},
            "tickets": {},
            "uhoh": {},
            "header": {
                "ip list": (By.CSS_SELECTOR, 'a[title="Partners"][href="#/partners"]'),
                "sp list": (By.CSS_SELECTOR, 'a[title="Service Providers"][href="#/service-providers"]'),
                "groupings": (By.CSS_SELECTOR, 'a[title="Groupings"][href="#/groupings"]'),
                "view profile":(By.CSS_SELECTOR, 'a[title="View Profile"]')
                }}
        targets = pages.get(page, {})
        # print(targets)
        if target is not None:
            return targets.get(target, ())
        else:
            return targets

    def check_starting_location(self, condition_id, function_name, user=None):
        """A wrapper around wait for page that exposes information about the proper location to call specific functions from.

        Args:
            condition_id: The condition to use from wait_for_page
            function_name: The name of the function that called it.
                (Often uses sys._getframe().f_code.co_name to automatically get function name)
            user: The user type to use for wait_for_page
        """
        if user is None:
            user="all"

        # Check location
        try:
            self.wait_for_page(condition_id, user_type=user, delay=5)
        except TimeoutException:
            err = "Error: Tried to start {0} while not on the create ticket page."
            raise TimeoutException(err.format(function_name))

    def login(self, user_type, user_num=0, wait_page="ticket tracking"):
        """
        Login through auth0 with a specific user.

        Args:
            user_type (str): Type of user (one of ["IP", "SP", "Admin"]
            user_num (int): The version of the user to use
                            Index starts at 0 (1 == second user)
        """
        # Start the actual login process
        driver = self.driver
        driver.get(path.join(self.civicdr_url, "#/logout"))
        driver.get(self.civicdr_url)
        user = get_user_creds(user_type, user_num)
        # Wait implicitly because of delayed loading of elements
        driver.implicitly_wait(10)
        # Enter email in login form
        email_elem = driver.find_element_by_name("email")
        email_elem.send_keys(user.email)
        # Enter IP password in login form
        pass_elem = driver.find_element_by_name("password")
        pass_elem.send_keys(user.password)
        pass_elem.send_keys(Keys.RETURN)
        # incorrect_login_string = "Wrong email or password."
        self.wait_for_page(wait_page, user_type=user_type, delay=10)


class ProfileTest(BaseTest):

    BASE_USER_TYPE = "all"
    PROFILE_LOCATION = "None"

    def get_to_initial_profile(self, user_type="IP"):
        """ Take an IP or SP to their initial profile creation page.

        Args:
            user_type (str): Type of user profile to get ("IP" || "SP")
        """
        driver = self.driver
        driver.get(self.civicdr_url)
        # Login
        self.login(user_type, user_num=0, wait_page="new profile")
        if user_type == "IP":
            # print("headed to new partners")
            driver.get(path.join(self.civicdr_url, "#/partners/new"))
        else:
            driver.get(path.join(self.civicdr_url, "#/service-providers/new"))
        self.wait_for_page("new profile", user_type, 10)

    def form_text_input(self, form_groups, key, val):
        """Fill out the text input field in a form.

        Args:
            form_groups: A array filled with selenium form elements
            key: The label text of the text input field to fill out
            val: the value to enter into that text input field
        """
        for form in form_groups:
            # print("in form_group")
            label_text = form.find_element_by_tag_name('label').text
            if label_text == key:
                # print("label == key")
                form_input = form.find_element_by_tag_name('input')
                form_input.clear()
                form_input.send_keys(val)

    def form_date(self, form_groups, key, val):
        """Fill out a date field in a form.

        Args:
            form_groups: A array filled with selenium form elements
            key: The label text of the date field to fill out
            val: the value to enter into that date field
        """
        for form in form_groups:
            # print("in form_group")
            label_text = form.find_element_by_tag_name('label').text
            if label_text == key:
                # print("label == key")
                form_input = form.find_element_by_tag_name('input')
                form_input.send_keys(val)

    def form_text_area(self, form_groups, key, val):
        """Fill out a text area field in a form.

        Args:
            form_groups: A array filled with selenium form elements
            key: The label text of the text area field to fill out
            val: the value to enter into that text area field
        """
        driver = self.driver
        for form in form_groups:
            label_text = form.find_element_by_tag_name('label').text
            if label_text == key:
                # print(key, label_text, "\n")
                form_input = form.find_element_by_tag_name('textarea')
                form_input.clear()
                setval_js = "arguments[0].value=`{0}`".format(val)
                driver.execute_script(setval_js, form_input)

    def form_checkbox(self, form_groups, key, options):
        """Fill out a checkbox field in a form.

        Args:
            form_groups: A array filled with selenium form elements
            key: The label text of the checkbox field to fill out
            options: the options to select in that checkbox field
        """
        driver = self.driver
        for form in form_groups:
            label_text = form.find_element_by_tag_name('label').text
            if label_text == key:
                # print(key, label_text, "\n")
                form_inputs = form.find_elements_by_tag_name('input')
                for option in form_inputs:
                    val = option.get_attribute('value')
                    # print(val)
                    if val in options:
                        # print("Selecting {0}".format(val))
                        driver.execute_script("arguments[0].click();",
                                              option)

    def form_radio(self, form_groups, key, val):
        """Fill out a radio field in a form.

        Args:
            form_groups: A array filled with selenium form elements
            key: The label text of the radio field to fill out
            val: the value to enter into that radio field
        """
        driver = self.driver
        for form in form_groups:
            label_text = form.find_element_by_tag_name('label').text
            if label_text == key:
                # print(key, label_text, "\n")
                form_select = form.find_elements_by_class_name('form__option--custom-radio')
                for option in form_select:
                    radio = option.find_element_by_class_name('form__option__text').text
                    if val == radio:
                        radio_input = option.find_element_by_tag_name('input')
                        driver.execute_script("arguments[0].click();",
                                              radio_input)

    def form_select(self, form_groups, key, option):
        """Fill out a select field in a form selecting the option by the value of the select element.

        Args:
            form_groups: A array filled with selenium form elements
            key: The label text of the select field to fill out
            option: the value of an option to select from the select field
        """
        for form in form_groups:
            label_text = form.find_element_by_tag_name('label').text
            # print(label_text)
            if label_text == key:
                select = Select(form.find_element_by_tag_name('select'))
                # for i in select.options:
                    # print(i.text)
                select.select_by_value(option)
                # select.select_by_visible_text(option)

    def form_select_visible(self, form_groups, key, option):
        """Fill out a select field in a form selecting the option by the visible text of the select element.

        Args:
            form_groups: A array filled with selenium form elements
            key: The label text of the select field to fill out
            option: the visible text of an option to select from the select field
        """
        for form in form_groups:
            label_text = form.find_element_by_tag_name('label').text
            # print(label_text)
            if label_text == key:
                select = Select(form.find_element_by_tag_name('select'))
                # for i in select.options:
                    # print(i.text)
                # select.select_by_value(option)
                select.select_by_visible_text(option)

    def complete_initial_profile(self, user_type, user_num=0, skip=[]):
        """ Goes to, and fills out an IP or SP inital profile. (Does not submit profile)
        Args:
            user_type: The type of user (IP/SP)
            user_num: The user number to use from the user config file and constants
            skip (array): Names of fields not to complete
        """
        self.get_to_initial_profile(user_type)
        self.fill_out_profile(user_type, user_num=user_num, skip=skip)

    def fill_out_profile(self, user_type, user_num=0, skip=[]):
        """ Fills out an IP or SP inital profile. (Does not submit profile)

        Args:
            user_type: The type of user (IP/SP)
            user_num: The user number to use from the user config file and constants
            skip (array): Names of fields not to complete
        """
        driver = self.driver
        user_info = get_user_info(user_type, user_num)
        # Text Fields
        form_groups = driver.find_elements(By.CLASS_NAME, "form__group")
        for key, val in user_info.get("text_input", {}).items():
            if key in skip:
                continue
            self.form_text_input(form_groups, key, val)
        # Text Areas
        for key, val in user_info.get("text_area", {}).items():
            if key in skip:
                continue
            self.form_text_area(form_groups, key, val)
        # Select Fields
        # Add checkbox elements for notification preferences
        checkbox_elements = driver.find_elements(By.CLASS_NAME, "checkboxes-light")
        for i in checkbox_elements:
            if i not in form_groups:
                form_groups.append(i)
        for key, options in user_info.get("checkbox", {}).items():
            # print(key, options)
            if key in skip:
                continue
            self.form_checkbox(form_groups, key, options)
        for key, option in user_info.get("select", {}).items():
            # print(key, options)
            if key in skip:
                continue
            self.form_select(form_groups, key, option)
        for key, options in user_info.get("radio", {}).items():
            # print(key, options)
            if key in skip:
                continue
            self.form_radio(form_groups, key, options)


    def get_profile_field(self, field_name):
        """ Gets a field from the profile form.
        Args:
            field_name: The visible name of the field to return
        """
        driver = self.driver
        # Text Fields
        form = None
        label = driver.find_elements_by_tag_name('label')
        for l in label:
            if l.text == field_name:
                form = l.find_element_by_xpath('..')
        if form is None:
            raise ValueError("No field of name \"{0}\" exists".format(field_name))
        else:
            return form

    def create_profile(self, user_type):
        """Goes to, fills out, and submits an IP or SP inital profile.
        Args:
            user_type: The type of user (IP/SP)
        """
        self.complete_initial_profile(user_type)
        # Return clicks on the Save button
        driver = self.driver
        self.save_profile()
        self.wait_for_page("ticket tracking", delay=10)

    def save_profile(self):
        """ Save a profile that has been filled out.
        """
        driver = self.driver
        submit_button = driver.find_element_by_css_selector(
            'input[type="submit"][value="Save"]')
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(submit_button, 0, 10)
        submit_button.click()

    def get_test_user_href(self, user_type, user_num=0):
        driver = self.driver
        user_info = get_user_info(user_type, user_num=user_num)
        user_name = user_info.get("text_input").get("Name")
        self.login("Admin")
        button_target = self.get_page_targets("header",
                                            "{0} list".format(user_type))
        user_list_button = driver.find_element(button_target[0],
                                               button_target[1])
        user_list_button.click()
        self.wait_for_page("{0} list".format(user_type), "Admin", 10)
        card_target = self.get_page_targets("{0}s".format(user_type),
                                      "card")
        # print(card_target)
        cards = driver.find_elements(card_target[0],
                                    card_target[1])
        users = get_usernames(user_type)
        for card in cards:
            title = card.find_element_by_tag_name("h1").text
            if title == user_name:
                content = card.find_element_by_class_name('card__content')
                return content.get_attribute('href')

    def delete_all_test_users(self):
        driver = self.driver
        driver.get(self.civicdr_url)
        self.login("Admin")
        # Check and delete IPs
        for user_type in ["IP", "SP"]:
            button_target = self.get_page_targets("header",
                                                "{0} list".format(user_type))
            user_list_button = driver.find_element(button_target[0],
                                                   button_target[1])
            user_list_button.click()
            self.wait_for_page("{0} list".format(user_type), "Admin", 10)
            card_target = self.get_page_targets("{0}s".format(user_type),
                                          "card")
            # print(card_target)
            cards = driver.find_elements(card_target[0],
                                        card_target[1])
            users = get_usernames(user_type)
            ticket_hrefs = []
            for card in cards:
                title = card.find_element_by_tag_name("h1").text
                if title in users:
                    content = card.find_element_by_class_name('card__content')
                    ticket_hrefs.append(content.get_attribute('href'))
            for href in ticket_hrefs:
                self.delete_profile_by_href(href)
                self.wait_for_page("{0} list".format(user_type), "Admin", delay=10)

    def delete_profile_by_href(self, href, delete_tickets=True):
        driver = self.driver
        driver.get(self.civicdr_url)
        # go to the users profile page
        driver.get(href)
        self.wait_for_page("profile", delay=10)
        if delete_tickets is True:
            # print("deleting tickets")
            self.delete_all_tickets_from_profile()
        # print("tickets deleted")
        # Delete Profile
        buttons = driver.find_elements_by_tag_name('button')
        for b in buttons:
            if b.text == "Delete":
                b.click()
                break
        # Selects first delete-modal on the page (user-deletion modal)
        self.wait_for_page("user delete modal", "Admin", delay=10)
        delete_modal = driver.find_element_by_class_name("delete-modal")
        del_buttons = delete_modal.find_elements_by_class_name("button")
        for b in del_buttons:
            if b.text == "Delete":
                b.click()
                break
        # input("Now HERE")
        # print("Deleted Profile")


    def delete_profile(self, user_type, user_num=0, delete_tickets=True):
        """Switch to admin and delete user profile.

        Args:
            user_type: The type of user (IP/SP)
            user_num: The user number to use from the user config file and constants
            delete_tickets: If the admin should delete IP user tickets first.
        """
        driver = self.driver
        driver.get(self.civicdr_url)
        # Wait until logged in
        self.wait_for_page("ticket tracking", delay=5)
        prof_target = self.get_page_targets("header", "view profile")
        profile_link = driver.find_element(prof_target[0],
                                           prof_target[1])
        profile_path = profile_link.get_attribute('href')
        print(profile_path)
        driver.get(path.join(self.civicdr_url, "#/logout"))

        # Wait until logged out
        # pause = input('COMPLETED PROFILE STUFF')
        # driver.find_elements_by_id('auth0-lock-container-1')
        self.wait_for_page("login", delay=10)

        # Login as Admin
        self.login("Admin", user_num=user_num)
        self.delete_profile_by_href(profile_path,
                                    delete_tickets=delete_tickets)
        self.wait_for_page("{0} list".format(user_type), "Admin", delay=10)
        driver.get(path.join(self.civicdr_url, "#/logout"))
        self.wait_for_page("login", "Admin", 10)

        # go to the users profile page
        # driver.get(profile_path)
        # self.wait_for_page("profile", delay=10)
        # if delete_tickets is True:
        #     print("deleting tickets")
        #     self.delete_all_tickets_from_profile()
        # print("tickets deleted")
        # # Delete Profile
        # buttons = driver.find_elements_by_tag_name('button')
        # for b in buttons:
        #     if b.text == "Delete":
        #         b.click()
        #         break
        # # Selects first delete-modal on the page (user-deletion modal)
        # self.wait_for_page("user delete modal", "Admin", delay=10)
        # delete_modal = driver.find_element_by_class_name("delete-modal")
        # del_buttons = delete_modal.find_elements_by_class_name("button")
        # for b in del_buttons:
        #     if b.text == "Delete":
        #         b.click()
        #         break
        # # input("Now HERE")
        # print("Deleted Profile")
        # self.wait_for_page("{0} list".format(user_type), "Admin", delay=10)
        # driver.get(path.join(self.civicdr_url, "#/logout"))
        # self.wait_for_page("login", "Admin", 10)


    def delete_all_tickets_from_profile(self):
        """Delete all tickets from a IP's profile

        Must start on the IP's profile page
        """
        # Wait until in profile
        self.check_starting_location("profile",
                                        sys._getframe().f_code.co_name)
        driver = self.driver
        # Delete Tickets
        # input("before profile deletion")
        select_all = driver.find_element_by_id('form-checkbox-1')
        driver.execute_script("arguments[0].click();",
                                              select_all)
        all_unbounded_buttons = driver.find_elements_by_class_name('button--unbounded')
        for i in all_unbounded_buttons:
            if i.text == "Delete":
                i.click()
        self.wait_for_page("ticket delete modal", "Admin", delay=10)
        dashboard_section = driver.find_element_by_css_selector('section[class="dashboard"]')
        warning_group = dashboard_section.find_element_by_css_selector('div[class="warning__group"]')
        all_unbounded_buttons = warning_group.find_elements_by_tag_name('button')
        for b in all_unbounded_buttons:
            if b.text == "Delete":
                b.click()
        # input("before profile deletion")

    def recreate_ip_profile(self):
        """Delete and recreate an IP.
        """
        # Setup by deleting IP
        driver = self.driver
        self.login("Admin", user_num=0)
        # Delete IP if they already exist
        if self.user_exists("IP") is True:
            # print("IP Exists")
            self.login("IP")
            self.delete_profile("IP")
            self.login("Admin", user_num=0)
        else:
            driver.get(self.civicdr_url)
            # print("IP Does Not Exist")
        self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, 10)
        partners_button = driver.find_element_by_css_selector(
            'a[title="Partners"][href="#/partners"]')
        partners_button.click()
        self.wait_for_page("IP list", "Admin", 10)
        # Create new IP
        new_partner_button = driver.find_element_by_css_selector(
            'a[href="#/partners/new"]')
        new_partner_button.click()
        self.wait_for_page("new profile", "IP", 10)
        self.fill_out_profile("IP", user_num=0)
        # Add IP Auth0 credentials
        ip_creds = get_user_creds("IP")
        openid = driver.find_element_by_id('form-openid')
        openid.send_keys("auth0|{0}".format(ip_creds.uuid))
        self.save_profile()
        self.wait_for_page("ticket tracking", delay=10)

    def recreate_profile(self, user_type):
        """Delete and recreate a user profile
        """
        # Setup by deleting user
        driver = self.driver
        self.login("Admin", user_num=0)
        # Delete user if they already exist
        if self.user_exists(user_type) is True:
            # print("User Exists")
            self.login(user_type)
            self.delete_profile(user_type)
            self.login("Admin", user_num=0)
        else:
            driver.get(self.civicdr_url)
            # print("User Does Not Exist")
        self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, 10)
        button_target = self.get_page_targets("header",
                                              "{0} list".format(user_type))
        user_list_button = driver.find_element(button_target[0],
                                               button_target[1])
        user_list_button.click()
        self.wait_for_page("{0} list".format(user_type), "Admin", 10)
        # Create new IP
        new_target = self.get_page_targets("{0}s".format(user_type), "new")
        new_button = driver.find_element(new_target[0],
                                         new_target[1])
        new_button.click()
        self.wait_for_page("new profile", user_type, 10)
        self.fill_out_profile(user_type, user_num=0)
        # Add IP Auth0 credentials
        ip_creds = get_user_creds(user_type)
        openid = driver.find_element_by_id('form-openid')
        openid.send_keys("auth0|{0}".format(ip_creds.uuid))
        self.save_profile()
        self.wait_for_page("ticket tracking", delay=10)

    def user_exists(self, user_type, user_num=0):
        """ Check if a user exists.

        Requires Admin user to be logged in
        """
        user_info = {"IP": {"admin_button": 'a[title="Partners"][href="#/partners"]',
                            "list_identifier": "IP list"},
                     "SP": {"admin_button": 'a[title="Service Providers"][href="#/service-providers"]',
                            "list_identifier": "SP list"}}
        info = user_info.get(user_type)
        exists = False
        driver = self.driver
        driver.get(self.civicdr_url)
        name = get_user_info(user_type, user_num)["text_input"]["Name"]
        creds = get_user_creds(user_type)
        # Go to user list page
        button = driver.find_element_by_css_selector(info.get('admin_button'))
        button.click()
        self.wait_for_page(info.get('list_identifier'), "Admin", 10)
        #  Find all  user elements
        users = driver.find_elements_by_tag_name('h1')
        for i in users:
            if i.text == name:
                a_obj = i.find_element_by_xpath('../..')
                a_obj.click()
                self.wait_for_page("profile", "Admin", 10)
                openid = driver.find_element_by_id('form-openid')
                val = openid.get_attribute('value')
                if val == "auth0|{0}".format(creds.uuid):
                    exists = True
                break
        return exists

def skipUnlessHasattr(obj, attr):
    if hasattr(obj, attr):
        return lambda func: func
    return unittest.skip("{!r} doesn't have {!r}".format(obj, attr))


class NewProfile(ProfileTest):

    def setUp(self):
        if self.BASE_USER_TYPE == "all":
            raise unittest.SkipTest("Skipping base test")
        self.civicdr_url = get_variable("BASE_URL")
        self.driver = webdriver.Chrome()
        self.addCleanup(self.driver.close)
        # Make sure we start anew every time
        self.delete_all_test_users()

        # try:
        #     self.login(self.BASE_USER_TYPE, user_num=0, wait_page="new profile")
        #     # print("NOT FOUND")
        #     profile_found = False
        # except TimeoutException:
        #     # print("FOUND")
        #     profile_found = True
        # if profile_found is True:
        #     try:
        #         # print("Waiting")
        #         self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, delay=5)
        #         # print("Deleting")
        #         self.delete_profile(self.BASE_USER_TYPE)
        #     except TimeoutException:
        #         print("An error occured. If a profile is not found the user should already have an account")

    def tearDown(self):
        self.login("Admin", user_num=0)
        if self.user_exists("IP") is True:
            # print("IP Exists")
            self.login("IP")
            self.delete_profile("IP")
        if self.user_exists("SP") is True:
            # print("IP Exists")
            self.login("SP")
            self.delete_profile("SP")

    def test_profile_on_login(self):
        """Test that a user encounters the profile creator on login.
        """
        driver = self.driver
        driver.get(self.civicdr_url)
        # Wait for next page to load
        try:
            self.login(self.BASE_USER_TYPE, user_num=0, wait_page="new profile")
        except TimeoutException:
            self.fail("Not taken to new partner url on creation")

    def test_after_failed_new_profile_base_url_to_new(self):
        """Test that the default url will take a user to the profile page until they create a profile

        See: CiviCDR Issue #14
          - https://github.com/ASL-19/civicdr/issues/14
        """
        self.get_to_initial_profile(self.BASE_USER_TYPE)
        driver = self.driver
        driver.get(self.civicdr_url)
        try:
            self.wait_for_page("new profile", self.BASE_USER_TYPE, 10)
        except TimeoutException:
            self.fail("{0} was not redirected to new profile screen after starting and stopping ticket creation (See CiviCDR Issue #14)".format(self.BASE_USER_TYPE))

    def test_required_values(self):
        """
        Tests that profiles cannot be created without all required values
        """
        # self.get_to_initial_profile()
        driver = self.driver
        required = self.PROFILE_REQUIRED
        for req in required:
            # driver.get(path.join(self.civicdr_url, "#/partners/new"))
            #pause = input('Trying {0}'.format(req))
            try:
                self.complete_initial_profile(self.BASE_USER_TYPE, skip=[req])
                submit_button = driver.find_element_by_css_selector(
                'input[type="submit"][value="Save"]')
                actions = ActionChains(driver)
                actions.move_to_element_with_offset(submit_button, 0, 10)
                submit_button.click()
                self.wait_for_page("new profile", self.BASE_USER_TYPE, 10)
            except TimeoutException:
                self.fail("IP Profile allowed submission without a required value {0}".format(req))

    def test_profile_creation(self):
        """Test the profile creation process
        """
        driver = self.driver
        try:
            self.create_profile(self.BASE_USER_TYPE)
        except TimeoutException:
            self.fail("Profile was not successfully created")
        headline_div = driver.find_element_by_class_name('inpage__headline')
        headline_text = headline_div.find_element_by_tag_name('h1').text
        self.assertEqual("CiviCDR Ticket Tracking",
                          headline_text,
                          "IP was not taken to ticket tracker upon profile creation")

    def test_deleteable(self):
        """Create and delete a profile to ensure it clears user-info
        """
        self.create_profile(self.BASE_USER_TYPE)
        self.wait_for_page("ticket tracking", delay=10)
        self.delete_profile(self.BASE_USER_TYPE)
        try:
            self.login(self.BASE_USER_TYPE, user_num=0, wait_page="new profile")
        except TimeoutException:
            self.fail("Profile was not successfully deleted")


class TicketManip(ProfileTest):

    def setUp(self):
        self.civicdr_url = get_variable("BASE_URL")
        self.driver = webdriver.Chrome()
        self.addCleanup(self.driver.close)
        self.delete_all_test_users()

    def start_ticket(self, user_type=None):
        """Takes an Admin or IP user to the page where they can create a new ticket
        """
        if user_type is None:
            user_type = self.BASE_USER_TYPE
        driver = self.driver
        driver.get(self.civicdr_url)
        self.wait_for_page("ticket tracking", user_type, 10)
        new_ticket_button = driver.find_element_by_css_selector(
            'button[class="button button--base"]')
        new_ticket_button.click()

    def save_ticket(self):
        """ Saves a ticket that has been filled out

        Requires that the user is on the ticket page
        """
        self.check_starting_location("create ticket",
                                     sys._getframe().f_code.co_name)
        driver = self.driver
        # Submit form
        submit_button = driver.find_element_by_css_selector(
            'input[type="submit"][value="Save"]')
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(submit_button, 0, 10)
        submit_button.click()
        self.wait_for_page("create ticket", self.BASE_USER_TYPE, 10)

    def complete_ticket(self, ticket_info, ip_num=0, skip=[], ticket_uuid=None):
        """Fills out ticket information
        """
        self.check_starting_location("create ticket",
                                     sys._getframe().f_code.co_name)
        driver = self.driver
        self.start_ticket()
        form_groups = driver.find_elements(By.CLASS_NAME, "form__group")
        # Radios
        for key, val in ticket_info.get("radio", {}).items():
            if key in skip:
                continue
            self.form_radio(form_groups, key, val)
        # IP Name
        ip_name = get_user_info("IP", ip_num)["text_input"]["Name"]
        self.form_select_visible(form_groups, "Implementing Partner", ip_name)
        # Text input
        for key, val in ticket_info.get("text_input", {}).items():
            if key in skip:
                continue
            self.form_text_input(form_groups, key, val)
        # text area
        for key, val in ticket_info.get("text_area", {}).items():
            if key in skip:
                continue
            self.form_text_area(form_groups, key, val)
        # Checkboxes
        for key, options in ticket_info.get("checkbox", {}).items():
            # print(key, options)
            if key in skip:
                continue
            self.form_checkbox(form_groups, key, options)
        # Date
        for key, val in ticket_info.get("date", {}).items():
            if key in skip:
                continue
            self.form_date(form_groups, key, val)
        # Add ticket UUID if requested
        if ticket_uuid is not None:
            team_member_input = driver.find_element_by_id("form-ticket_ip_name")
            team_member_input.clear()
            team_member_input.send_keys(ticket_uuid)


    def setup_ticket_scenerio(self):
        """Creates an IP and a ticket

        Used to setup most ticket scenarios
        """
        # Create Required IP Account
        self.recreate_ip_profile()
        self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, 10)
        created_ticket = self.create_ticket()
        return created_ticket

    def filter_tickets(self, filter_type, value):
        """Filters the tickets in the ticketing interface

        filter_type (str): The type of filter to use.
            ["type", "status", "grouping"]
        value (str): The option to select from the filter (only selects a single option)
        """
        types = ["type", "status", "grouping"]
        driver = self.driver
        filter_parent = driver.find_element_by_class_name('filters--status')
        children = filter_parent.find_elements_by_xpath("./child::*")
        # filter_groups = driver.find_elements_by_class_name('filters__group')
        filter_grouping = None
        for i, child in enumerate(children):
            if child.text == filter_type.upper():
                filter_grouping = children[i+1]
                break
        if filter_grouping is None:
            raise ValueError("Could not find filter group of type: {0}".format(filter_type))
        for label in filter_grouping.find_elements_by_tag_name("label"):
            text = label.find_element_by_class_name("form__option__text").text
            if value == text:
                checkbox = filter_grouping.find_element_by_tag_name("input")
                driver.execute_script("arguments[0].click();",
                                          checkbox)
                return True
        return False

    def get_tickets_by_date(self, date):
        """Get ticket elements from the ticket list that were updated on a specific date.
        """
        driver = self.driver
        matches = []
        cards = driver.find_elements_by_class_name('card__content')
        for card in cards:
            updated = card.find_element_by_class_name('card__updated')
            card_date = re.search("\d{4}-\d{2}-\d{2}", updated.text ).group()
            if date == card_date:
                matches.append(card)
        return matches

    def ticket_matches_uuid(self, href, uuid):
        """Check if a ticket uses a specific UUID in the 'IP Contact Name'

        Args:
            href (string): the url of the ticket to check
            uuid (string): the UUID to check for in the 'IP Contact Name' field
        """
        #print("TICKET HREF = {0}".format(href))
        driver = self.driver
        driver.get(href)
        self.wait_for_page("ticket view", self.BASE_USER_TYPE, 10)
        fields = driver.find_elements_by_class_name('profile-fields')
        for field in fields:
            title = field.find_element_by_class_name('field__title').text
            if title == "IP Contact Name":
                #print("Found IP Contact Name")
                link = field.find_element_by_tag_name('p')
                #print("User Name = {0}".format(link.text))
                if link.text == uuid:
                    return True
        return False

    def get_ticket_by_uuid(self, ticket_info, ticket_uuid):
        """Get the href of a ticket that matches a specific UUID

        Args:
            ticket_info: The tickets info (per: utils.get_ticket_info())
            ticket_uuid: The uuid of the ticket
        """
        self.check_starting_location("ticket tracking",
                                     sys._getframe().f_code.co_name)
        #print("TICKET UUID {0}".format(ticket_uuid))
        self.filter_tickets("type", ticket_info['checkbox']["Incident Type"][0])
        self.filter_tickets("status", ticket_info['radio']["Status"])
        todays_date = datetime.today().strftime("%Y-%m-%d")
        todays_tickets = self.get_tickets_by_date(todays_date)
        ticket_hrefs = []
        created_ticket = None
        for ticket in todays_tickets:
            ticket_hrefs.append(ticket.get_attribute('href'))
        #print("ALL HREFS")
        #print(ticket_hrefs)
        for ticket_href in ticket_hrefs:
            if self.ticket_matches_uuid(ticket_href, ticket_uuid):
                created_ticket = ticket_href
                break
        return created_ticket

    def create_ticket(self):
        """Create an IP and a ticket.
        This is used as a setup function by more advanced ticket functionality functions
        """
        driver = self.driver
        self.wait_for_page("ticket tracking", self.BASE_USER_TYPE, 10)
        self.start_ticket("IP")
        ticket_info = get_ticket_info(0)
        ticket_uuid = uuid4().hex
        self.complete_ticket(ticket_info, ticket_uuid=ticket_uuid)
        self.save_ticket()
        self.wait_for_page("ticket tracking", delay=10)
        created_ticket = self.get_ticket_by_uuid(ticket_info, ticket_uuid)
        return created_ticket

    def assign_sp_to_ticket(self, sp_num=0):
        """Assign an SP to a ticket.
        """
        self.check_starting_location("ticket view",
                                     sys._getframe().f_code.co_name)
        driver = self.driver
        sp_info = get_user_info("SP", user_num=sp_num)
        buttons = driver.find_elements_by_tag_name('button')
        for button in buttons:
            if button.text == "Assign a Provider":
                button.click()
                break
        self.wait_for_page("sp ticket filter modal", delay=10)
        form_groups = driver.find_elements_by_class_name('form__group')
        for form in form_groups:
            label = form.find_element_by_tag_name('label').text
            if label == "Service Provider":
                select = Select(form.find_element_by_tag_name('select'))
                select.select_by_visible_text(sp_info['text_input']["Name"])
                break
        buttons = driver.find_elements_by_tag_name('button')
        for button in buttons:
            if button.text == "Assign Provider":
                button.click()
                break
        self.wait_for_page("sp assigned to ticket", delay=10)
