import pandas as pd
import pandas_market_calendars as pm_calendar
import numpy as np
from urllib.parse import urlencode
import requests
import os
import copy
from ...stock_trend.data_acquisitor import DataAcquisitor


class BondETFDataAcquisitor(DataAcquisitor):

	def _get_market(self) -> str:
		'''
		获得ETF交易市场
		'''
		if self._secid[0] == '5':
			return 'SH'
		else:
			return 'SZ'
	
	def _gen_secid(self) -> str:
		'''
		生成东方财富专用的secid

		Return
		------
		str: 指定格式的字符串
		'''

		# 深市ETF
		if self._code[0] != '5':
			return f'0.{self._code}'
		# 沪市ETF
		return f'1.{self._code}'
