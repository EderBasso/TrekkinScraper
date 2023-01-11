import os
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import psycopg2
from psycopg2 import OperationalError


def create_connection():
    conn = None
    try:
        credentials = open('db.credentials', 'r')
        db_name = credentials.readline().strip('\n\r')
        db_user = credentials.readline().strip('\n\r')
        db_password = credentials.readline().strip('\n\r')
        db_host = credentials.readline().strip('\n\r')
        db_port = credentials.readline().strip('\n\r')
        credentials.close()

        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(e)
    return conn


connection = create_connection()

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

items = []
print(len(lista))
for each_item in lista:
    id = each_item.get_attribute('id')
    descricao = each_item.find_element(By.CLASS_NAME, 'BoxPriceName').find_element(By.TAG_NAME, 'a').text
    preco = each_item.find_element(By.CLASS_NAME, 'BoxPriceValor').text
    imagem = each_item.find_element(By.CLASS_NAME, 'imagen_buscador').get_attribute('src')
    link = each_item.find_element(By.CLASS_NAME, 'prod_list').get_attribute('href')
    item = [id, descricao, preco, imagem, link]
    items.append(item)
    print(id + ' - ' + descricao + ' - ' + preco + ' - ' + link)

for each_record in items:
    insert_query = """ INSERT INTO sapatilhas_masc (id, descricao, preco, imagem, link) VALUES (%s,%s,%s,%s,%s)"""
    record = (each_record[0],each_record[1],each_record[2],each_record[3],each_record[4])
    cursor = connection.cursor()
    cursor.execute(insert_query, record)
    connection.commit()
    count = cursor.rowcount
    print(count, "Item inserio na tabela")
    break

cursor.close()
connection.close()
browser.quit()
