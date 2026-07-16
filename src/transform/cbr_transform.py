"""
Преобразования данных курсов валют ЦБ.
"""
import pandas as pd

TARGET_CURRENCY_CODES = [
   'USD',
   'EUR',
   'JPY',
   'CNY'
]

def filter_target_currencies(
   currency_rates_df: pd.DataFrame
) -> pd.DataFrame:
   """
   Оставить только USD, EUR, JPY, CNY
   """
   filtered_currency_rates_df = (
       currency_rates_df
       .loc[
           currency_rates_df['currency_code'].isin(
               TARGET_CURRENCY_CODES
           )
       ]
       .copy()
   )
   return filtered_currency_rates_df