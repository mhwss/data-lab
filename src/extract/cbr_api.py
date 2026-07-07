"""
Функции для получения и парсинга курсов валют ЦБ РФ.

Модуль отвечает только за:
- запрос XML у ЦБ;
- парсинг XML;
- получение курсов за одну дату.

Модуль не отвечает за:
- циклы по периодам;
- добавление технических полей;
- загрузку в ClickHouse.
"""

from datetime import date
import urllib3
import xml.etree.ElementTree as ET

import pandas as pd
import requests


CBR_URL = 'https://www.cbr.ru/scripts/XML_daily.asp'

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


def fetch_cbr_xml(request_date: date) -> str:
    """
    Получить XML с курсами валют ЦБ за указанную дату.
    """

    request_params = {
        'date_req': request_date.strftime('%d/%m/%Y')
    }

    cbr_api_response = requests.get(
        CBR_URL,
        params=request_params,
        timeout=30,
        verify=False
    )

    cbr_api_response.raise_for_status()

    return cbr_api_response.text


def parse_cbr_exchange_rates(cbr_xml_text: str) -> pd.DataFrame:
    """
    Преобразовать XML ЦБ в pandas DataFrame.
    """

    xml_root = ET.fromstring(cbr_xml_text)

    rate_date = pd.to_datetime(
        xml_root.attrib['Date'],
        format='%d.%m.%Y'
    )

    currency_rows = []

    for currency_xml in xml_root.findall('Valute'):
        currency_rows.append({
            'rate_date': rate_date,
            'currency_code': currency_xml.findtext('CharCode'),
            'currency_name': currency_xml.findtext('Name'),
            'nominal': int(currency_xml.findtext('Nominal')),
            'rate': float(
                currency_xml.findtext('Value').replace(',', '.')
            )
        })

    currency_rates_df = pd.DataFrame(currency_rows)

    return currency_rates_df


def get_cbr_rates_by_date(request_date: date) -> pd.DataFrame:
    """
    Получить курсы валют ЦБ за одну дату.
    """

    cbr_xml_text = fetch_cbr_xml(request_date)

    currency_rates_df = parse_cbr_exchange_rates(
        cbr_xml_text
    )

    return currency_rates_df