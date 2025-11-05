import os
import numpy as np
import pandas as pd
import pandas_market_calendars as pm_calendar
from security_tools.stock_trend import DataAcquisitor
from security_tools.stock_trend import DataAnalyzer

def analyze_stock_data(code: str, startDate: str, endDate: str, inDir: str, priceLimit: np.float64):
	dataAcquisitor = DataAcquisitor(code, startDate, endDate, 1, inDir = inDir)
	dataAnalyzer = DataAnalyzer(dataAcquisitor)
	signal = dataAnalyzer.get_signal(priceLimit)
	url   = dataAnalyzer.get_data_acquired().get_quotation_url()
	return signal, url

def analyze_stock_data_multiprocess(param):
	return analyze_stock_data(*param)

def run_data_analyzer(nproc: int, codes: list[str], names: list[str], startDate: str, endDate: str, inDir: str, outDir: str, outPrefix: str, priceLimit: np.float64):
    from multiprocessing import Pool
    import itertools
    from tqdm.auto import tqdm

    size = len(codes)
    with Pool(nproc) as pool:
        print("分析T+0期信号")
        signals, urls = zip(*tqdm(pool.imap(analyze_stock_data_multiprocess,
        				zip(codes, itertools.repeat(startDate), itertools.repeat(endDate), itertools.repeat(inDir), itertools.repeat(priceLimit))),
        				total = size))
        signals = np.array([*signals])
        marketCalendar = pm_calendar.get_calendar('XSHG').schedule(start_date = startDate, end_date = endDate)
        signalsOld = np.zeros((signals.shape[0], 2), dtype = int)
        endDateOld = endDate
        for i in range(signalsOld.shape[1]):
            endDateOld = pd.to_datetime(endDateOld) - pd.Timedelta(days = 1)
            while not endDateOld in marketCalendar.index:
        	    if os.path.exists(f"{outDir}/{outPrefix}_{endDateOld.strftime('%Y%m%d')}.csv"):
        		    break
        	    endDateOld = endDateOld - pd.Timedelta(days=1)
            endDateOld = endDateOld.strftime("%Y%m%d")
            if i == 0: endDateOld0 = endDateOld
            print("分析T-" + str(i+1) + "期信号")
            signalsOld[:,i], _ = zip(*tqdm(pool.imap(analyze_stock_data_multiprocess,
        	                     zip(codes, itertools.repeat(startDate), itertools.repeat(endDateOld), itertools.repeat(inDir), itertools.repeat(priceLimit))),
        	                     total = size))

    print(f"保存购买信号......")
    df = pd.DataFrame({"股票简称":names.values, "行情地址": urls,
                       "购买信号": signals, "上期信号": signalsOld[:, 0], "上上期信号": signalsOld[:, 1],
                       "上期备注": ['' for i in range(len(codes))], "备注": ['' for i in range(len(codes))]},
                       index = pd.Index(codes, name = "股票代码"))
    df.sort_values(by = ["购买信号","上期信号", "上上期信号", "股票代码"], axis = 0, ascending = False, inplace = True) # by = [col2, col1] means sort col1 first, then col2
    try: 
        dfOld = pd.read_csv(f"{outDir}/{outPrefix}_{endDateOld0}.csv", dtype = {"股票代码": str, "备注": str})
        dfOld.set_index("股票代码", inplace=True)
        df["上期备注"] = dfOld["备注"]
    except:
        print("You must be too lazy to analyze stock price data every business day :(")
    finally:
        df.to_csv(f"{outDir}/{outPrefix}_{endDate}.csv")

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1].isdigit():
        nproc = int(sys.argv[1])
    else:
        nproc = None

    # 开始日期
    startDate = "20190101"
    # 结束日期
    endDate   = pd.to_datetime("today").strftime("%Y%m%d")
    # 输入路径
    inDir     = "stock_price_data"
    # 保存路径
    signalsDir = "long_short_signals"
    # 价格限制
    priceLimit = 9999.0

    '''
    # example candlestick plot
    dataAcquisitor = DataAcquisitor("000157", startDate, endDate, False, 1, inDir = inDir)
    dataAnalyzer = DataAnalyzer(dataAcquisitor)
    dataAnalyzer.plot_MA_and_K("day")
    dataAnalyzer.plot_MA_and_K("week")
    dataAnalyzer.plot_MA_and_K("month")
    '''

    # 保存路径
    signalsPrefix = "signalsCSIA500"
    # 股票代码
    df = pd.read_csv('stock_codes/CSIA500_component_codes_exBFRE.csv', dtype = {0: str})
    headerCode = df.columns[0]
    headerName = df.columns[1]
    codes = df[headerCode]
    names = df[headerName]

    print(f"正在分析中证A500成分股的k线数据......")
    run_data_analyzer(nproc, codes, names, startDate, endDate, inDir, signalsDir, signalsPrefix, priceLimit)
