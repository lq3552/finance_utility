import pandas as pd
import pandas_market_calendars as pm_calendar
import numpy as np
from urllib.parse import urlencode
import requests
import os
import copy


## TODO: using inheritance from stock DataAcquisitor, but first this tool must be package-ized
class BondETFDataAcquisitor(object):

	'''
	静态成员，东方财富网爬取数据相关变量
	参考：Micro-sheep https://zhuanlan.zhihu.com/p/350578719
	'''
	__EastmoneyKlines = {
        'f51': 'Date',
        'f52': 'Open',
        'f53': 'Close',
        'f54': 'High',
        'f55': 'Low',
        'f56': 'Volume',
        'f57': '成交额',
        'f58': '振幅',
        'f59': '涨跌幅',
        'f60': '涨跌额',
        'f61': '换手率',
	}
	__EastmoneyHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'http://quote.eastmoney.com/center/gridlist.html'
	}
	__fields = list(__EastmoneyKlines.keys())
	__columns = list(__EastmoneyKlines.values())[1:]
	__fields2 = ",".join(__fields)
	__dateFormat = "%Y%m%d"
	__emptyDataFrame = pd.DataFrame(columns = __columns, index = [pd.Timestamp.min])
	_QuotationURLHeader = "https://xueqiu.com/S/"

	class UnsupportedDataFrameError(BaseException):
		pass

	def __init__(self, code: str, beg: str, end: str, mode: int = 0, inDir: str = None, outDir: str = "."):
		'''
		参数
			code :  6 位ETF代码
			beg:    开始日期 例如 20200101
			end:    结束日期 例如 20200201
			mode:   0 - 在线 1 - 离线
			inDir:  输入数据文件夹路径
			outDir: 输出数据文件夹路径
		'''
		self._code  = code
		self._secid = self._gen_secid()
		self._beg   = beg
		self._end   = end
		self._mode  = mode
		self._XD    = False

		self._outDir = outDir
		if inDir == None:
			inDir = outDir
		self._inDir = inDir
		self.read_from_csv(mode)
		if mode == 0:
			self._dayK   = self._get_k_history(klt = 101, setXDFlag = True)
			self._dayK   = self._get_k_history(klt = 101)
			self._weekK  = self._get_k_history(klt = 102)
			self._monthK = self._get_k_history(klt = 103)

	def get_code(self) -> str:
		'''
		get stock code
		'''
		return self._code

	def get_quotation_url(self) -> str:
		'''
		get stock quotation URL
		'''
		return BondETFDataAcquisitor._QuotationURLHeader + self._get_market() + self._code

	def _get_market(self) -> str:
		'''
		获得ETF交易市场
		'''
		if self._secid[0] == '5':
			return 'SH'
		else:
			return 'SZ'
	
	def get_day_k(self) -> pd.DataFrame:
		return self._dayK 

	def get_week_k(self) -> pd.DataFrame:
		return self._weekK 

	def get_month_k(self) -> pd.DataFrame:
		return self._monthK 

	def read_from_csv(self, mode: int):
		'''
		参数
			mode: 0 - 在线 1 - 离线
		'''
		try:
			if mode == 0:
				beg = pd.Timestamp.min
				end = pd.Timestamp.max
			else:
				beg = self._beg
				end = self._end

			self._dayK   = pd.read_csv(f"{self._inDir}/{self._code}_day.csv", encoding="utf-8-sig",
									   parse_dates = [0], index_col = 0, dtype = np.float64).loc[beg : end]
			self._weekK  = pd.read_csv(f"{self._inDir}/{self._code}_week.csv", encoding="utf-8-sig",
									   parse_dates = [0], index_col = 0, dtype = np.float64).loc[beg : end]
			self._monthK = pd.read_csv(f"{self._inDir}/{self._code}_month.csv", encoding="utf-8-sig",
									   parse_dates = [0], index_col = 0, dtype = np.float64).loc[beg : end]

			if self._dayK.empty or self._weekK.empty or self._monthK.empty:
				raise self.UnsupportedDataFrameError()

		except (FileNotFoundError, self.UnsupportedDataFrameError):
			self._dayK   = copy.deepcopy(self.__emptyDataFrame)
			self._weekK  = copy.deepcopy(self.__emptyDataFrame)
			self._monthK = copy.deepcopy(self.__emptyDataFrame)

	def save_to_csv(self):
		if self._mode == 1: # saving is not supported in the offline mode
			return
		if not os.path.exists(self._outDir):
			os.makedirs(f"{self._outDir}")
		self._dayK.to_csv(f"{self._outDir}/{self._code}_day.csv", encoding="utf-8-sig")
		self._weekK.to_csv(f"{self._outDir}/{self._code}_week.csv", encoding="utf-8-sig")
		self._monthK.to_csv(f"{self._outDir}/{self._code}_month.csv", encoding="utf-8-sig")

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
	
	def _get_k_history(self, klt: int = 101, fqt: int = 1, setXDFlag: bool = False) -> pd.DataFrame:
		'''
		功能获取k线数据
		-
		参数
	        klt: k线间距 默认为 101 即日k
	            klt:1 1 分钟
	            klt:5 5 分钟
	            klt:101 日
	            klt:102 周
				klt:103 月
	        fqt: 复权方式
	            不复权 : 0
	            前复权 : 1
	            后复权 : 2 
		'''

		if klt == 101:
			dfOld = self._dayK
		elif klt == 102:
			dfOld = self._weekK
		elif klt == 103:
			dfOld = self._monthK
		else: # unsupported
			return copy.deepcopy(self.__emptyDataFrame)

		# only keep the dates of new records
		begOld = dfOld.index[0]
		beg = pd.DatetimeIndex([self._beg])[0]
#		if beg < begOld: # prepend not supported yet
#			dfOld = copy.deepcopy(self.__emptyDataFrame)
		if True: # only fetch new data and append them to old data
			endOld = dfOld.index[-1]
			end = pd.DatetimeIndex([self._end])[0]
			if endOld > end:
				return dfOld
			# if today is not ex-dividend day then there is no need to update everything before
			if not self._XD: 
				beg = max(beg, endOld)
			# Check if the dates of new records are all holidays. If so, then there is no need to update.
			marketCalendar = pm_calendar.get_calendar('XSHG').schedule(start_date = beg, end_date=end)
			checkDate = beg + pd.Timedelta(days=1)
			while(checkDate <= end):
				if checkDate in marketCalendar.index:
					break
				checkDate += pd.Timedelta(days=1)
			if checkDate > end:
				return dfOld

			beg = beg.strftime(self.__dateFormat)

		# used to check ex-dividend day
		if klt == 101 and setXDFlag == True:
			if pd.isnull(dfOld.iloc[0,1]):
				closePriceOld = np.nan
			else:
				closePriceOld = dfOld.iloc[-1,1]
		# drop the last row, because it could be updated in the case of week/month K
		dfOld.drop(dfOld.index[-1], inplace = True)

		params = (
	        ("fields1", "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13"),
	        ("fields2", self.__fields2),
	        ("beg", beg),
	        ("end", self._end),
	        ("rtntype", '6'),
	        ("secid", self._secid),
	        ("klt", f"{klt}"),
	        ("fqt", f"{fqt}"),
		)
		params = dict(params)
		base_url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
		url = base_url+'?'+urlencode(params)
		json_response: dict = requests.get(
	        url, headers = self.__EastmoneyHeaders).json()
	
		data = json_response.get('data')
		if data is None:
			if self._secid[0] == '0':
				self._secid = f"1.{self._code}"
			else:
				self._secid = f"0.{self._code}"
			params["secid"] = self._secid
			url = base_url + '?' + urlencode(params)
			json_response: dict = requests.get(
				url, headers = self.__EastmoneyHeaders).json()
			data = json_response.get("data")
		if data is None:
			print("ETF代码:", self._code, "可能有误")
			return copy.deepcopy(self.__emptyDataFrame)
	
		klines = data['klines']

		index = []
		rows  = dfOld.loc[self._beg : self._end].to_numpy().tolist() if not self._XD else []
		for _kline in klines:
			kline = _kline.split(',')
			index.append(kline[0])
			rows.append(kline[1:])

		# XD must be decided by dayK in the current version
		if klt == 101 and setXDFlag == True:
			# ex-dividend day encountered, must update everything before, only set the XD flag here
			# limitation: DataAcquisitor has to be run every day, otherwise it is guaranteed re-download the table!
			if ~np.isnan(closePriceOld) and rows[-1][1] != closePriceOld:
				self._XD = True
				return copy.deepcopy(self.__emptyDataFrame)

		index = pd.DatetimeIndex(index)
		if not self._XD:
			index = pd.DatetimeIndex([*dfOld.index, *index])
	
		df = pd.DataFrame(rows, columns = self.__columns, index = index)

		return df


def acquire_and_save_bondETF_data(code: str, startDate: str, endDate: str, outDir: str):
	print(f"正在获取 {code} 从 {startDate} 到 {endDate} 的 k线数据......")
	# 根据ETF代码、开始日期、结束日期获取指定ETF代码指定日期区间的k线数据
	dataAcquisitor = BondETFDataAcquisitor(code, startDate, endDate, False, 0, outDir = outDir)
	# 保存k线数据到表格里面
	print(f"ETF代码：{code} 的 k线数据已保存到指定目录 {outDir} 下的csv 文件中")
	dataAcquisitor.save_to_csv()

	
if __name__ == "__main__":
	from multiprocessing import Pool
	nproc = 8
	import itertools
	from tqdm.auto import tqdm

	# ETF代码
	code = "511090"
	# 开始日期
	startDate = "20230616"
	# 结束日期
	endDate   = pd.to_datetime("today").strftime("%Y%m%d")
	# 输出路径
	outDir    = "bondETF_price_data"
	acquire_and_save_bondETF_data(code, startDate, endDate, outDir)
