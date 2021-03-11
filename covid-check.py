#!/usr/bin/env python3
import time
import random
import pprint
import sys
import yaml
import subprocess
import re
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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

def getCenters(row):
    data = {}
    cell_mapping = {
            '1': "name",
            '2': "county",
            '3': "location",
            '4': "address",
            '5': "available_slots",
            '6': "actions"
        }
    cells = row.find_elements_by_xpath(".//mat-cell")
    cell_counter = 1
    for cell in cells:
        print(" ---- Cell ----\n")
        pp.pprint(cell)
        spans = cell.find_elements_by_xpath(".//span")
        for span in spans:
            print(" --- Span ---\n")
            #print(span.text)
            print(span.get_attribute("innerHTML"))
            data[cell_mapping[str(cell_counter)]] = span.get_attribute("innerHTML")
        mat_chips = cell.find_elements_by_xpath(".//mat-chip")
        for mat_chip in mat_chips:
            print(" --- MAT-CHIP ---\n")
            
            places = mat_chip.get_attribute("innerHTML")
            m = re.search('\s*([0-9]+)\s*$', places)
            if(m.group(1)):
                places = m.group(1)
            data[cell_mapping[str(cell_counter)]] = places
        buttons = cell.find_elements_by_xpath(".//button")
        if(len(buttons) >= 1):
            #see if buttons[0] is enabled or disabled
            state = buttons[0].is_enabled()
            print("Button is "+str(state))
            data[cell_mapping[str(cell_counter)]] = buttons[0].is_enabled()
            data["program_action"] = buttons[0]
        cell_counter+=1
    return data

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
                data["program_action"] = buttons[1]

             
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

                    #click the button to see which centers are available
                    button = data['program_action']
                    print("Clicking on Programeaza for "+user+"...\n")
                    #scroll the browser view to have the button visible
                    ActionChains(driver).move_to_element(button).perform()
                    #wait for the element to be visible...
                    element = WebDriverWait(driver, 20).until(EC.visibility_of(button))
                    driver.save_screenshot("6-recipients-"+user+".png")
                    #click on it
                    element.click()
                    time.sleep(10)
                    
                    centers = []
                    
                    # handle pagination
                    page = 0
                    while True:
                        table_rows = driver.find_elements(By.XPATH, "//mat-row")
                        for row in table_rows:
                            print(" == Row centers ==\n")
                            pp.pprint(row)
                            center_data = getCenters(row)
                            centers.append(center_data)
                        
                        if page > 10:
                            print("Stopping after 10 pages\n")
                            break
                        
                        # look if the next page is active
                        next_button_list = driver.find_elements(By.XPATH, "//button[@aria-label='Următoarea pagină']")
                        if len(next_button_list) > 0:
                            next_button = next_button_list[0] #just take the first (and only) match
                            #scroll the browser view to have the button visible
                            ActionChains(driver).move_to_element(next_button).perform()
                            #wait for the element to be visible...
                            element = WebDriverWait(driver, 20).until(EC.visibility_of(next_button))
                            driver.save_screenshot("7-centers-"+user+"-page-"+str(page)+".png")
                            state = element.is_enabled()
                            if(state):
                                #load next page and do the loop
                                #click on it
                                element.click()
                                time.sleep(10)
                                page+=1
                            else:
                                print("Reached the last center page for "+user+"\n")
                                break
                        else:
                            print("Couldn't find next button")
                            break
                    print("Found centers: \n")
                    pp.pprint(centers)
 

                    # go through all the centers, 
                    
                    available = ""
                    bingo = ""
                    for center in centers:
                        # are there centers with available places?
                        if int(center['available_slots']):
                            available += center['name'] + "(" + center['available_slots'] + "), "
                            # are there places defined in the yaml?    
                            for pl in conf['centers']:
                                if re.search(pl, center.name):
                                   bingo += center['name'] + "(" + center['available_slots'] + "), " 
                        
                    if (bingo != ""):
                        message = "User "+user+" can make a covid appointment!" + bingo
                        subprocess.run([conf['external_program'], message], stdout=subprocess.PIPE, universal_newlines=True)    
                    elif (available != ""):
                        message = "User "+user+" can make a covid appointment! Centers with available slots: " + available
                        subprocess.run([conf['external_program'], message], stdout=subprocess.PIPE, universal_newlines=True)
                    
                    
                    #exit after one user (I know, it's lame, but it's quick and dirty and prevents me from keeping state)
                    sys.exit()
finally:

    driver.quit()
