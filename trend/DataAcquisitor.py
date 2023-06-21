from urllib.parse import urlencode
import pandas as pd
import requests

class DataAcquisitor(object):

	'''
	静态成员，东方财富网爬取数据相关变量
	'''
	EastmoneyKlines = {
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
	EastmoneyHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'http://quote.eastmoney.com/center/gridlist.html'
	}
	fields = list(EastmoneyKlines.keys())
	columns = list(EastmoneyKlines.values())
	fields2 = ",".join(fields)

	def __init__(self, code: str, beg: str, end: str, mode: int = 0, inDir: str = ".", outDir: str = "."):
		'''
		参数
			code :  6 位股票代码
			beg:    开始日期 例如 20200101
			end:    结束日期 例如 20200201
			mode:   0 - 在线 1 - 离线
			inDir:  输入数据文件夹路径
			outDir: 输出数据文件夹路径
		'''
		self.code  = code
		self._secid = self._gen_secid()
		self.beg   = beg
		self.end   = end

		self.inDir = inDir
		self.outDir = outDir
		if mode == 0:
			self.dayK  = self._get_k_history(klt = 101)
			self.weekK  = self._get_k_history(klt = 102)
			self.monthK  = self._get_k_history(klt = 103)
		else:
			self.read_from_csv()

	def read_from_csv(self):
		self.dayK =   pd.read_csv(f"{self.inDir}/{self.code}_day.csv", encoding="utf-8-sig")
		self.weekK =  pd.read_csv(f"{self.inDir}/{self.code}_week.csv", encoding="utf-8-sig")
		self.monthK = pd.read_csv(f"{self.inDir}/{self.code}_month.csv", encoding="utf-8-sig")

	def save_to_csv(self):
		self.dayK.to_csv(f"{self.outDir}/{self.code}_day.csv", encoding="utf-8-sig", index=None)
		self.weekK.to_csv(f"{self.outDir}/{self.code}_week.csv", encoding="utf-8-sig", index=None)
		self.monthK.to_csv(f"{self.outDir}/{self.code}_month.csv", encoding="utf-8-sig", index=None)

	def _gen_secid(self) -> str:
	    '''
	    生成东方财富专用的secid
	
	    Parameters
	    ----------
	
	    Return
	    ------
	    str: 指定格式的字符串
	
	    '''
	    # 沪市指数
	    if self.code[:3] == '000':
	        return f'1.{self.code}'
	    # 深证指数
	    if self.code[:3] == '399':
	        return f'0.{self.code}'
	    # 沪市股票
	    if self.code[0] != '6':
	        return f'0.{self.code}'
	    # 深市股票
	    return f'1.{self.code}'
	
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
	    params = (
	        ("fields1", "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13"),
	        ("fields2", self.fields2),
	        ("beg", self.beg),
	        ("end", self.end),
	        ("rtntype", '6'),
	        ("secid", self._secid),
	        ("klt", f"{klt}"),
	        ("fqt", f"{fqt}"),
	    )
	    params = dict(params)
	    base_url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
	    url = base_url+'?'+urlencode(params)
	    json_response: dict = requests.get(
	        url, headers = self.EastmoneyHeaders).json()
	
	    data = json_response.get('data')
	    if data is None:
	        if self._secid[0] == '0':
	            self._secid = f"1.{self.code}"
	        else:
	            self._secid = f"0.{self.code}"
	        params["secid"] = self._secid
	        url = base_url + '?' + urlencode(params)
	        json_response: dict = requests.get(
	            url, headers = self.EastmoneyHeaders).json()
	        data = json_response.get("data")
	    if data is None:
	        print("股票代码:", self.code, "可能有误")
	        return pd.DataFrame(columns = self.columns)
	
	    klines = data['klines']
	
	    rows = []
	    for _kline in klines:
	
	        kline = _kline.split(',')
	        rows.append(kline)
	
	    df = pd.DataFrame(rows, columns = self.columns)
	
	    return df


if __name__ == "__main__":
	df = pd.read_csv('stock_codes/CSI300_component_codes.csv', dtype = {0: str})
	header = df.columns[0]
	# 股票代码
	codes = df[header] #["002230"] 

	# 开始日期
	start_date = "20200621"
	# 结束日期
	end_date   = "20230621"
	
	i = 0
	for code in codes:
		print(f"{i}正在获取 {code} 从 {start_date} 到 {end_date} 的 k线数据......")
		# 根据股票代码、开始日期、结束日期获取指定股票代码指定日期区间的k线数据
		dataAcquisitor = DataAcquisitor(code, start_date, end_date, 0, outDir = "stock_price_data")
		dataAcquisitor.save_to_csv()
		# 保存k线数据到表格里面
		print(f"股票代码：{code} 的 k线数据已保存到指定目录下的 {code}.csv 文件中")
		i += 1
