
# CiviCDR Testing Suite

Functionality and unit testing for the CiviCDR platform.

CiviCDR Testing is a functionality and unit testing suite for the CiviCDR platform, written using the Selenium library. It was created to ensure that platform functionality was maintained as new features and bug fixes are introduced.

In the future we will integrate this into the [CI process](https://stackoverflow.com/questions/35218005/running-python-selenium-tests-on-circleci) to ensure regressions in functionality are automatically identified.

# Features

Functionality tests for Implementing Partner, Administrator, and Service Provider roles.

# Requirements

Python3
Selenium
Selenium Chrome Web Driver

# Installation

This testing suite is currently downloaded and run by hand.

```sh
sudo -H pip3 install selenium
git clone https://github.com/ASL-19/civicdr-test.git
cd civicdr_testing
```

# Usage

## Setup

### Create Users

Before running the tests you need to create test users in the Auth0 interface. You will need:

- 1 IP users
- 2 SP users
- 1 Admin Users

### Populate the config file

You need to have a config file in `config/config.conf`. You will need to add a configuration file there that includes details about your user and the URL to test.

There is a base configuration file in `config/test.conf`. You can copy that to config.conf to use it as a starting place.

```bash
cp config/test.conf config/config.conf
```

For each of the users in the `[user]` section you will need to add their Auth0 email and password to the configuration file.

```
IP_EMAIL_0 = [YOUR IP EMAIL HERE]
IP_PASS_0 = [YOUR IP PASSWORD HERE]
```

In the `[config]` section you will need to add the base URL for the civicdr platform. In this example we have a testing platform hosted at test_platform.civicdr.org .

```
BASE_URL = https://test_platform.civicdr.org
```


## Running Tests


To run all tests and see their success and failure you simply run the following command from the base directory.

```sh
python3 civicdr_testing/init_tests.py -v
python3 civicdr_testing/unit_tests.py -v
```

# License

Please see the [license file](https://github.com/ASL-19/civicdr-test/blob/master/LICENSE) for license information on CiviCDR Testing. If you have further questions related to licensing PLEASE create an issue about it on github.
