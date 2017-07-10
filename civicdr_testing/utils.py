#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of CiviCDR Testing, a functionality testing suite for CiviCDR.
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

import configparser
from collections import namedtuple
from os import getenv, path
from constants import user_info_constants, EXAMPLE_TICKETS


def get_usernames(user_type):
    usernames = []
    for user in user_info_constants.get(user_type):
        usernames.append(user.get("text_input").get("Name"))
    return usernames


def get_user_info(user_type, user_num=0):
    user_info = user_info_constants[user_type][user_num]
    # print(type(user_info))
    # print(dir(user_info))
    # print(user_info)
    return user_info

def get_ticket_info(ticket_num):
    ticket_info = EXAMPLE_TICKETS[ticket_num]
    return ticket_info


def get_user_creds(user_type, user_num=0):
    UserConfig = namedtuple('User', ['email', 'password', "uuid"])
    users = {"IP":"IP", "SP":"SP", "ADMIN":"Admin"}
    try:
        cur_user = users[user_type.upper()]
        email_var = "{0}_EMAIL_{1}".format(cur_user, int(user_num))
        pass_var = "{0}_PASS_{1}".format(cur_user, int(user_num))
        uuid_var = "{0}_ID_{1}".format(cur_user, int(user_num))
    except KeyError as _e:
        raise ValueError("Unknown user type {0}".format(user_type))
    except ValueError as _e:
        raise ValueError("user_num must be an int, not {0}".format(user_num))
    try:
        email = get_from_config('user', email_var)
        password = get_from_config('user', pass_var)
        uuid = get_from_config('user', uuid_var)
    except ValueError: # Not in config, try env variables
        email = getenv(email_var)
        password = getenv(pass_var)
        uuid = getenv(uuid_var)
        if email is None:
            raise ValueError("Variable {0} not set".format(email_var))
        elif password is None:
            raise ValueError("Variable {0} not set".format(pass_var))
        elif uuid is None:
            raise ValueError("Variable {0} not set".format(uuid_var))
    user = UserConfig(email, password, uuid)
    return user


def get_from_config(section_name, var_name):
    config_path = getenv("CONFIG_PATH")
    if config_path is None:
        cur_path = path.dirname(path.abspath(__file__))
        config_path = path.join(cur_path, '../config/config.conf')
    config = configparser.ConfigParser()
    config.read(config_path)
    try:
        var = config[section_name][var_name]
        return var
    except KeyError:
        raise ValueError("{0} variable {1} not set".format(section_name,
                                                           var_name))


def get_variable(variable_name):
    var = None
    try:
        var = get_from_config('config', variable_name)
    except ValueError: # Not in config, try env variables
        var = getenv(variable_name)
    if var is None:
        raise ValueError("Variable {0} not set".format(var))
    return var
