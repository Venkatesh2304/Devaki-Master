from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login(url,user,pwd,dbName) : 
    driver = webdriver.Chrome("../chromedriver.exe")
    driver.get(f"{url}/rsunify/")
    for [k,v] in [["userName",user],["databaseName",dbName],["password",pwd]] : 
        WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID,k ))
        ) 
        driver.execute_script(f"document.getElementById(\"{k}\").value = \"{v}\"")
    WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID,"gologin"))
    ).click()
    WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID,"gologin"))
    )
    driver.execute_script("pageSubmit()")
    return  driver.get_cookie("JSESSIONID")["value"] 