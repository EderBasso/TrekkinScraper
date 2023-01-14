import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

import psycopg2
from psycopg2 import OperationalError

import datetime

import os
from dotenv import load_dotenv
load_dotenv()


def create_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT")
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(e)
    return conn


def select_all(table_name):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        select_query = "select * from {}".format(table_name)
        cursor.execute(select_query)
        entries = cursor.fetchall()
        entries_dict = {}
        for entry in entries:
            entries_dict.update({entry[0]:entry})
        return entries_dict
    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()


def insert_items(items, table_name):
    if len(items) <= 0:
        print(f"Nenhum item novo para inserir na tb {table_name}")
        return
    try:
        connection = create_connection()
        cursor = connection.cursor()
        insert_query = f""" INSERT INTO {table_name} (id, descricao, preco, imagem, link, data_atual) VALUES (%s, %s, %s, %s, %s, %s)"""
        print(insert_query % items[0])
        result = cursor.executemany(insert_query, items)
        connection.commit()
        count = cursor.rowcount
        #print(count, f"Item inserio na tabela {table_name}")
    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL{}".format(error))
    finally:
        if connection:
            cursor.close()
            connection.close()


def update_items(items, table_name):
    if len(items) <= 0:
        print(f"Nenhum item alterado para atualizar na tb {table_name}")
        return
    try:
        connection = create_connection()
        cursor = connection.cursor()
        update_query = f""" UPDATE {table_name} SET descricao = %s, preco = %s, imagem = %s, link = %s,
         data_atual = %s, preco_anterior = %s, data_anterior = %s 
         WHERE id = %s"""
        result = cursor.executemany(update_query, items)
        connection.commit()
        count = cursor.rowcount
        print(count, f"Item atualizado na tabela {table_name}")
    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL{}".format(error))
    finally:
        if connection:
            cursor.close()
            connection.close()


chrome_driver = 'C:/chromedriver/chromedriver.exe'
chrome_service = Service(chrome_driver)
chrome_options = Options()
chrome_options.add_argument('--headless')

browser = webdriver.Chrome(service=chrome_service, options=chrome_options)
browser.get('https://www.tradeinn.com/trekkinn/pt/calcado-homem-sapatos-escalada/14264/s')

wait = WebDriverWait(browser, 5)
wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'li_position_p')))

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

produtos = []
date_time = datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp())
for each_item in lista:
    id = each_item.get_attribute('id')
    descricao = each_item.find_element(By.CLASS_NAME, 'BoxPriceName').find_element(By.TAG_NAME, 'a').text
    preco = each_item.find_element(By.CLASS_NAME, 'BoxPriceValor').text
    imagem = each_item.find_element(By.CLASS_NAME, 'imagen_buscador').get_attribute('src')
    link = each_item.find_element(By.CLASS_NAME, 'prod_list').get_attribute('href')
    item = (id, descricao, preco, imagem, link, date_time)
    produtos.append(item)
    ##print(id + ' - ' + descricao + ' - ' + preco + ' - ' + link)

records_db = select_all('sapatilhas_masc')

lista_insert = []
lista_update = []
for produto_site in produtos:
    if produto_site[0] in records_db.keys():
        produto_base = records_db.get(produto_site[0])
        if produto_base[2] != produto_site[2]:
            temp_tuple = (produto_site[1], produto_site[2], produto_site[3], produto_site[4], produto_site[5],
                          produto_base[2], produto_base[5], produto_site[0])
            lista_update.append(temp_tuple)
    else:
        lista_insert.append(produto_site)


insert_items(lista_insert, 'sapatilhas_masc')
update_items(lista_update, 'sapatilhas_masc')

browser.quit()
