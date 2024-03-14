import pandas as pd
import sys

def index_set_difference(argv, inplace = False):
	if inplace and len(argv) < 3:
		print("ERROR: require names of 2 existing tables!")
		return
	if not inplace and len(argv) < 4:
		print("ERROR: require names of 2 existing tables and 1 tables for the result of set difference!")
		return

	tableMinuend = pd.read_csv(argv[1], dtype = {"股票代码": str})
	tableMinuend.set_index("股票代码", inplace = True)
	tableSubtrahend = pd.read_csv(argv[2], dtype = {"股票代码": str})
	tableSubtrahend.set_index("股票代码", inplace = True)
	if inplace:
		tableResultName = argv[1]
	else:
		tableResultName = argv[3]
	
	tableResult = tableMinuend.drop(tableSubtrahend.index)
	tableResult.to_csv(tableResultName)


if __name__ == "__main__":
	index_set_difference(sys.argv, inplace = False)
