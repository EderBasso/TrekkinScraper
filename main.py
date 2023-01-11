import os
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

chrome_driver = 'C:/chromedriver/chromedriver.exe'
chrome_service = Service(chrome_driver)
chrome_options = Options()
chrome_options.add_argument('--headless')

browser = webdriver.Chrome(service=chrome_service, options=chrome_options)
browser.get('https://www.tradeinn.com/trekkinn/pt/calcado-homem-sapatos-escalada/14264/s')

wait = WebDriverWait(browser, 5)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'li_position_p')))

webElementUl = browser.find_element(By.ID, 'items')
lista = webElementUl.find_elements(By.CLASS_NAME, 'li_position_p')

temNovos = True
while temNovos:
    browser.execute_script(script='cargar_mas();')
    sleep(10)

    webElementUl = browser.find_element(By.ID, 'items')
    lista2 = webElementUl.find_elements(By.CLASS_NAME, 'li_position_p')
    if len(lista2) != len(lista):
        lista = lista2
    else:
        temNovos = False

print(len(lista))
for each_item in lista:
    descricao= each_item.find_element(By.CLASS_NAME, 'BoxPriceName').find_element(By.TAG_NAME, 'a').text
    preco = each_item.find_element(By.CLASS_NAME, 'BoxPriceValor').text
    print(descricao + ' - ' + preco)
browser.quit()