from urllib.parse import urlencode
import pandas as pd
import requests
import os
import copy

class DataAcquisitor(object):

	'''
	静态成员，东方财富网爬取数据相关变量
	'''
	__EastmoneyKlines = {
        'f51': '日期',
        'f52': '开盘',
        'f53': '收盘',
        'f54': '最高',
        'f55': '最低',
        'f56': '成交量',
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
	__emptyDataFrame = pd.DataFrame(columns = __columns, index = pd.DatetimeIndex(["1900-01-01"]))
	_QuotationURLHeader = "https://xueqiu.com/S/"

	class UnsupportedDataFrameError(BaseException):
		pass

	def __init__(self, code: str, beg: str, end: str, isIndex: bool = False, mode: int = 0, inDir: str = None, outDir: str = "."):
		'''
		参数
			code :  6 位股票代码
			beg:    开始日期 例如 20200101
			end:    结束日期 例如 20200201
			mode:   0 - 在线 1 - 离线
			mode:   0 - 在线 1 - 离线
			inDir:  输入数据文件夹路径
			outDir: 输出数据文件夹路径
		'''
		self._code  = code
		self._isIndex = isIndex
		self._secid = self._gen_secid(isIndex)
		self._beg   = beg
		self._end   = end

		self._outDir = outDir
		if inDir == None:
			inDir = outDir
		self._inDir = inDir
		self.read_from_csv()
		if mode == 0:
			self._dayK  = self._get_k_history(klt = 101)
			self._weekK  = self._get_k_history(klt = 102)
			self._monthK  = self._get_k_history(klt = 103)

	def get_code(self) -> str:
		'''
		get stock code
		'''
		return self._code

	def get_quotation_url(self) -> str:
		'''
		get stock quotation URL
		'''
		return DataAcquisitor._QuotationURLHeader + self._get_market() + self._code

	def _get_market(self) -> str:
		'''
		获得股票交易市场
		'''
		if self._secid[0] == '0':
			return 'SZ'
		else:
			return 'SH'
	
	def get_day_k(self) -> pd.DataFrame:
		return self._dayK 
	def get_week_k(self) -> pd.DataFrame:
		return self._weekK 
	def get_month_k(self) -> pd.DataFrame:
		return self._monthK 

	def read_from_csv(self):
		try:
			self._dayK   = pd.read_csv(f"{self._inDir}/{self._code}_day.csv", encoding="utf-8-sig", parse_dates = [0], index_col = 0)
			self._weekK  = pd.read_csv(f"{self._inDir}/{self._code}_week.csv", encoding="utf-8-sig", parse_dates = [0], index_col = 0)
			self._monthK = pd.read_csv(f"{self._inDir}/{self._code}_month.csv", encoding="utf-8-sig", parse_dates = [0], index_col = 0)
			if self._dayK.empty or self._weekK.empty or self._monthK.empty:
				raise self.UnsupportedDataFrameError()
		except (FileNotFoundError, self.UnsupportedDataFrameError):
			self._dayK   = copy.deepcopy(self.__emptyDataFrame)
			self._weekK  = copy.deepcopy(self.__emptyDataFrame)
			self._monthK = copy.deepcopy(self.__emptyDataFrame)

	def save_to_csv(self):
		if not os.path.exists(self._outDir):
			os.makedirs(f"{self._outDir}")
		self._dayK.to_csv(f"{self._outDir}/{self._code}_day.csv", encoding="utf-8-sig")
		self._weekK.to_csv(f"{self._outDir}/{self._code}_week.csv", encoding="utf-8-sig")
		self._monthK.to_csv(f"{self._outDir}/{self._code}_month.csv", encoding="utf-8-sig")

	def _gen_secid(self, isIndex: bool) -> str:
		'''
		生成东方财富专用的secid

		Parameters
		----------
		mode: 0 - 股票 1 - 指数
	
		Return
		------
		str: 指定格式的字符串
		'''

		if isIndex:
			# 沪市指数
			if self._code[:3] == '000':
				return f'1.{self._code}'
			# 深证指数
			if self._code[:3] == '399':
				return f'0.{self._code}'
		else:
			# 深市股票
			if self._code[0] != '6':
				return f'0.{self._code}'
			# 沪市股票
			return f'1.{self._code}'
	
	def _get_k_history(self, klt: int = 101, fqt: int = 1) -> pd.DataFrame:
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

		# find the date to append new rows
		begOld = dfOld.index[0]
		endOld = dfOld.index[-1]
		beg = pd.DatetimeIndex([self._beg])[0]
		end = pd.DatetimeIndex([self._end])[0]
		if endOld > end:
			return dfOld
		beg = max(beg, endOld)
		beg = beg.strftime(self.__dateFormat)
		dfOld.drop(dfOld.index[-1], inplace = True) # drop the last row, because it could be updated during the market opening hours

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
			print("股票代码:", self._code, "可能有误")
			return copy.deepcopy(self.__emptyDataFrame)
	
		klines = data['klines']

		index = []
		rows  = dfOld.to_numpy().tolist()
		for _kline in klines:
			kline = _kline.split(',')
			index.append(kline[0])
			rows.append(kline[1:])

		index = pd.DatetimeIndex(index)
		index = pd.DatetimeIndex([*dfOld.index, *index])
	
		df = pd.DataFrame(rows, columns = self.__columns, index = index)

		return df


if __name__ == "__main__":
	df = pd.read_csv('stock_codes/CSI300_component_codes.csv', dtype = {0: str})
	header = df.columns[0]
	# 股票代码
	codes = df[header]

	# 开始日期
	start_date = "20180621"
	# 结束日期
	end_date   = pd.to_datetime("today").strftime("%Y%m%d")
	size = len(codes)
	i = 1
	for code in codes:
		print(f"{i}/{size} 正在获取 {code} 从 {start_date} 到 {end_date} 的 k线数据......")
		# 根据股票代码、开始日期、结束日期获取指定股票代码指定日期区间的k线数据
		dataAcquisitor = DataAcquisitor(code, start_date, end_date, False, 0, outDir = "stock_price_data")
		dataAcquisitor.save_to_csv()
		# 保存k线数据到表格里面
		print(f"股票代码：{code} 的 k线数据已保存到指定目录下的 {code}.csv 文件中")
		i += 1
