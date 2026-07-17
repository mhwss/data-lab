"""
Преобразования данных курсов валют ЦБ.
"""
import pandas as pd

from src.config.settings import CBR_TARGET_CURRENCY_CODES

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
               CBR_TARGET_CURRENCY_CODES
           )
       ]
       .copy()
   )
   return filtered_currency_rates_df