import json
import sys
import os
import time
import string
import shutil
# from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
from icecream import ic

# with open('./credentials.json', 'r') as f:
#     credentials = json.load(f)

role = "Student" if not int(input('Enter role: 0. Student 1. Staff\n')) else "Staff"
username = input("Enter Username:\n")
password = input("Enter Password:\n")
credentials = dict(Role=role, Username=username, Password=password)

download_dir = os.path.join(os.getcwd(), 'Data')

chrome_options = Options()
chrome_options.add_experimental_option('prefs', {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False
})

driver = webdriver.Chrome(options=chrome_options)

def filename_generator(content_name: str):
    for special_character in string.punctuation:
        if special_character in content_name:
            content_name = content_name.replace(special_character, '')
    return '_'.join(content_name.lower().split())

def fillup_login_page(driver: webdriver.Chrome):
    driver.get('https://darshanums.in/Login.aspx')

    if credentials['Role'] == 'Student':
        driver.find_element(By.ID, "rblRole_1").click()
    elif credentials['Role'] == 'Staff':
        driver.find_element(By.ID, "rblRole_0").click()
    else:
        print('Role can be either "Student" or "Staff"')
        sys.exit()

    driver.find_element(By.ID, "txtUsername").send_keys(credentials["Username"])
    driver.find_element(By.ID, "txtPassword").send_keys(credentials["Password"])
    driver.find_element(By.ID, "btnLogin").click()


def load_semester(driver: webdriver.Chrome, semester: int):
    if semester not in range(1,9):
        print('Semester can only be between 1 to 8')
        sys.exit()

    driver.get("https://darshanums.in/StudentPanel/LMS/LMS_ContentStudentDashboard.aspx")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".select2-selection__arrow > b:nth-child(1)"))
    ).click()

    semester_ul =  driver.find_element(By.ID, "select2-ctl00_cphPageHeaderRight_ddlSemester-results")
    semester_ul.find_elements(By.TAG_NAME, 'li')[semester].click()

def wait_till_download():
    WAIT = True
    i = 0
    while True:
        for entry in os.scandir(download_dir):
            if entry.is_file() and not entry.name.endswith('crdownload'):
                WAIT = False

        if not WAIT or i > (60*2)*3 : break
        else:
            time.sleep(.5)
            i += 1

def save_downloaded_file_to(*, destination_dir: str, filename: str, indexer: int=0):
    os.makedirs(os.path.join(download_dir, destination_dir), exist_ok=True)
    for entry in os.scandir(download_dir):
        if entry.is_file():
            ext = entry.name.split('.')[-1]
            if not indexer:
                shutil.move(entry.path, os.path.join(download_dir, destination_dir, filename+'.'+ext))
            else:
                shutil.move(entry.path, os.path.join(download_dir, destination_dir, filename+str(indexer)+'.'+ext))

            break
    else:
        print('something went wrong in save_downloaded_file_to function')
        sys.exit()

if __name__ == '__main__':
    os.makedirs(download_dir, exist_ok=True)
    fillup_login_page(driver)

    for semester in range(1, 8):
        load_semester(driver, semester)

        try:
            subjects = driver.find_element(By.ID, "ctl00_cphPageContent_divSubjectWiseContentCount")
            num_subjects = len(subjects.find_elements(By.TAG_NAME, 'a'))
        except Exception as e:
            print('No more semesters', str(e), sep='\n')

        for i in range(num_subjects):
            subjects = driver.find_element(By.ID, "ctl00_cphPageContent_divSubjectWiseContentCount")
            subject = subjects.find_elements(By.TAG_NAME, 'a')[i]
            driver.get(str(subject.get_attribute("href")))

            try:
                nav_tabs = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-tabs"))
                )
                for tab in nav_tabs.find_elements(By.TAG_NAME, "li"):
                    if "Presentation" in (elem:=tab.find_element(By.TAG_NAME, "a")).text.strip():
                        elem.click()
                        break
                else:
                    raise exceptions.NoSuchElementException('Presentation not found')
                    
            except (exceptions.NoSuchElementException, exceptions.TimeoutException) as e:
                print(str(e))


            subject_name = filename_generator(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_cphPageHeader_lblPageHeader_XXXXX"))
            ).text.strip())
            table_rows = driver.find_elements(By.CSS_SELECTOR, "#Content0019 #tblSubjectWiseContentDetails > tbody > tr")[1:]
            for row in table_rows:
                filename = filename_generator(row.find_element(By.CSS_SELECTOR, 'span > a').text.strip())
                download_buttons = row.find_elements(By.CSS_SELECTOR, 'span > span')
                for idx, download_button in enumerate(download_buttons):
                    ActionChains(driver).move_to_element(download_button).click(download_button).perform()
                    wait_till_download()
                    time.sleep(.5)
                    save_downloaded_file_to(destination_dir=subject_name, filename=filename, indexer=idx)

                break

            load_semester(driver, semester)
    
    
    input("Press Enter key to exit...")