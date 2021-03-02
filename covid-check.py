#!/usr/bin/env python3
import time
import random
import pprint
import sys
import yaml
import subprocess
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

opts = Options()
opts.headless = True

try:
    conffile = sys.argv[1]
except IndexError as exc:
    print("Usage: python3 covid-check.py covid.yaml")
    sys.exit(1)

conf = {}
with open(conffile, 'r') as stream:
    try:
        conf = yaml.load(stream, Loader=yaml.SafeLoader)
    except yaml.YAMLError as exc:
        print(exc)
        print("Unable to parse configuration file "+conffile)
        sys.exit(1)


driver = Chrome(options=opts, executable_path=conf['chromepath'])
USERNAME=conf['username']
PASSWORD=conf['password']
pp = pprint.PrettyPrinter(indent=4)

try:
    driver.get('https://programare.vaccinare-covid.gov.ro/auth/login')
    print("loading page...\n")
    time.sleep(10)
    driver.save_screenshot("1-login.png")
    print("sending username...\n")
    driver.find_element_by_id('mat-input-0').send_keys(USERNAME)
    driver.save_screenshot("2-username.png")
    
    time.sleep(random.randint(1,5))
    print("sending password...\n")
    password_field = driver.find_element_by_id('mat-input-1')
    password_field.send_keys(PASSWORD)
    driver.save_screenshot("3-password.png")

    #send an Enter
    password_field.send_keys(Keys.RETURN)
    driver.save_screenshot("4-logging-in.png")
    time.sleep(10)
    driver.save_screenshot("5-after-login.png")
    # go to beneficiari page
    print("going to beneficiari...\n")
    driver.get("https://programare.vaccinare-covid.gov.ro/#/recipients")
    time.sleep(10)
    driver.save_screenshot("6-recipients.png")
    #table_rows = driver.find_elements(By.XPATH, "/html/body/app/vertical-layout-1/div/div/div/div/content/app-list-recipients/div/fuse-widget/div[2]/div/mat-table/mat-row*/mat-cell")
    table_rows = driver.find_elements(By.XPATH, "//mat-row")
    
    #table_cells = driver.find_elements(By.XPATH, "//mat-cell")
   
    patients = []

    for row in table_rows:
        print(" == Row ==\n")
        pp.pprint(row)
        data = {}
        
        cells = row.find_elements_by_xpath(".//mat-cell")
        cell_counter = 1
        cell_mapping = {
            '1': "name",
            '2': "cnp",
            '3': "id",
            '4': "added_by",
            '5': "actions"
        }
        for cell in cells:
            print(" ---- Cell ----\n")
            pp.pprint(cell)

            spans = cell.find_elements_by_xpath(".//span")
            for span in spans:
                print(" --- Span ---\n")
                #print(span.text)
                print(span.get_attribute("innerHTML"))
                data[cell_mapping[str(cell_counter)]] = span.get_attribute("innerHTML")

            buttons = cell.find_elements_by_xpath(".//button")
            if(len(buttons) > 2):
                #see if buttons[1] is enabled or disabled
                state = buttons[1].is_enabled()
                print("Button is "+str(state))
                data[cell_mapping[str(cell_counter)]] = buttons[1].is_enabled()

             
            cell_counter+=1
        patients.append(data)
    print("Dumping patients:\n")
    pp.pprint(patients)


    # search for wanted user status
    need_to_announce = False
    for user in conf['search']:
        print("User "+user+"\n")
        for patient in patients:
            if patient['name'] == user:
                print("Found user "+user+", button state is "+str(patient['actions'])+"\n")
                #button is active
                if(patient['actions'] == True):
                    message = "User "+user+" can make a covid appointment!"
                    subprocess.run([conf['external_program'], message], stdout=subprocess.PIPE, universal_newlines=True)
finally:

    driver.quit()
