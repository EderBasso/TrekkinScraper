import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import re
from decimal import Decimal

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


def select_all():
    try:
        connection = create_connection()
        cursor = connection.cursor()
        select_query = "select * from produtos"
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


def insert_items(items):
    if len(items) <= 0:
        print("Nenhum item novo para inserir na tb produtos")
        return
    try:
        connection = create_connection()
        cursor = connection.cursor()
        insert_query = """ INSERT INTO produtos (id, descricao, preco, imagem, link, data_atual) VALUES (%s, %s, %s, %s, %s, %s)"""
        #print(insert_query % items[0])
        result = cursor.executemany(insert_query, items)
        connection.commit()
        count = cursor.rowcount
        print(count, "Item inserio na tabela produtos")
    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL{}".format(error))
    finally:
        if connection:
            cursor.close()
            connection.close()

    try:
        connection = create_connection()
        cursor = connection.cursor()
        insert_query = """ INSERT INTO precos (id_produto, data, preco) VALUES (%s, %s, %s)"""
        lista_precos = []
        for item in items:
            tuple_precos = (item[0], item[5], item[2])
            lista_precos.append(tuple_precos)
        result = cursor.executemany(insert_query, lista_precos)
        connection.commit()
        count = cursor.rowcount
        print(count, "Item inserio na tabela precos")
    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL{}".format(error))
    finally:
        if connection:
            cursor.close()
            connection.close()


def update_items(items):
    if len(items) <= 0:
        print("Nenhum item alterado para atualizar na tb produtos")
        return
    try:
        connection = create_connection()
        cursor = connection.cursor()
        update_query = """UPDATE produtos SET descricao = %s, preco = %s, imagem = %s, link = %s, data_atual = %s WHERE id = %s"""
        result = cursor.executemany(update_query, items)
        connection.commit()
        count = cursor.rowcount
        print(count, "Item atualizado na tabela produtos")
    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL{}".format(error))
    finally:
        if connection:
            cursor.close()
            connection.close()

    try:
        connection = create_connection()
        cursor = connection.cursor()
        insert_query = """ INSERT INTO precos (id_produto, data, preco) VALUES (%s, %s, %s)"""
        lista_precos = []
        for item in items:
            tuple_precos = (item[5], item[4], item[1])
            lista_precos.append(tuple_precos)
        result = cursor.executemany(insert_query, lista_precos)
        connection.commit()
        count = cursor.rowcount
        print(count, "Item inserio na tabela precos")
    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL{}".format(error))
    finally:
        if connection:
            cursor.close()
            connection.close()

def converter_preco(preco_str):
    return Decimal(re.search("\d+.\d+", preco_str).group())

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
    preco = converter_preco(each_item.find_element(By.CLASS_NAME, 'BoxPriceValor').text)
    imagem = each_item.find_element(By.CLASS_NAME, 'imagen_buscador').get_attribute('src')
    link = each_item.find_element(By.CLASS_NAME, 'prod_list').get_attribute('href')
    item = (id, descricao, preco, imagem, link, date_time)
    produtos.append(item)
    #print(item)
    #break

records_db = select_all()

lista_insert = []
lista_update = []
for produto_site in produtos:
    if produto_site[0] in records_db.keys():
        produto_base = records_db.get(produto_site[0])
        if produto_base[2] != produto_site[2]:
            temp_tuple = (produto_site[1], produto_site[2], produto_site[3], produto_site[4], produto_site[5], produto_site[0])
            lista_update.append(temp_tuple)
    else:
        lista_insert.append(produto_site)


insert_items(lista_insert)
update_items(lista_update)

browser.quit()


def check_alerts(user):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        select_query = f""" SELECT * FROM produtos
            inner join alertas on produtos.id like alertas.id_produto
            where alertas.usuario like '{user}'"""
        cursor.execute(select_query)
        alertas = cursor.fetchall()

        for row in alertas:
            print("Id = ", row[0], )
            print("Model = ", row[1])
            print("Current Price  = ", row[2])
            print("Alert Price  = ", row[11], "\n")

    except (Exception, OperationalError) as error:
        print("Error while selecting data from SQL{}".format(error))
    finally:
        if connection:
            cursor.close()
            connection.close()


#check_alerts('eder')

