import pandas as pd
from security_tools.bond.bondETF_data_acquisitor import BondETFDataAcquisitor

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
	codes = ["511090", "511260", "511010"]
	# 开始日期
	startDate = "20230616"
	# 结束日期
	endDate   = pd.to_datetime("today").strftime("%Y%m%d")
	# 输出路径
	outDir    = "bondETF_price_data"
	for code in codes:
		acquire_and_save_bondETF_data(code, startDate, endDate, outDir)
