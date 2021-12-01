import yahoo_fin.stock_info as si

dow_list = si.tickers_dow()
print("Tickers in Dow Jones:", len(dow_list))
dow_list[0:10]

tickers = dow_list[0:10]

# list of tickers whose financial data needs to be extracted
financial_dir = {}
stats = ['ebit',
         'market_cap',
         'netIncome',
         'totalCashFromOperatingActivities',  # cashflow
         'capitalExpenditures',
         'totalAssets',
         'totalCurrentLiabilities',
         'propertyPlantEquipment',
         'totalStockholderEquity',
         "longTermDebt",
         'commonStock',  # treasuryStock',
         'minorityInterest',
         ]

for ticker in tickers:
    try:
        temp_dir = {}
        # getting balance sheet data from yahoo finance for the given ticker
        balance_sheet = si.get_balance_sheet(ticker).iloc[:, 0]
        for i in balance_sheet.index:
            if i in stats:
                temp_dir[i] = balance_sheet[i]

        # getting income statement data from yahoo finance for the given ticker
        income_statement = si.get_income_statement(ticker).iloc[:, 0]
        for i in income_statement.index:
            if i in stats:
                temp_dir[i] = income_statement[i]

        # getting cashflow statement data from yahoo finance for the given ticker
        cash_flow_statement = si.get_cash_flow(ticker).iloc[:, 0]
        for i in cash_flow_statement.index:
            if i in stats:
                temp_dir[i] = cash_flow_statement[i]
        # get market cap
        temp_dir['market_cap'] = si.get_quote_table(ticker)["Market Cap"]
        temp_dir['DivYield'] = si.get_quote_table(ticker)["Forward Dividend & Yield"]
        # combining all extracted information with the corresponding ticker
        financial_dir[ticker] = temp_dir
    except:
        print('{}: failed to gather data...'.format(ticker))

# storing information in pandas dataframe
combined_financials = pd.DataFrame(financial_dir)
combined_financials.dropna(how='all', axis=1, inplace=True)  # dropping columns with all NaN values
tickers = combined_financials.columns  # updating the tickers list based on only those tickers whose values were successfully extracted

# creating dataframe with relevant financial information for each stock using fundamental data
indx = ["EBIT", "MarketCap", "NetIncome", "CashFlowOps", "Capex", "CurrAsset",
        "CurrLiab", "PPE", "BookValue", "TotDebt", "PrefStock", "MinInterest", "DivYield"]
all_stats = {}
for ticker in tickers:
    try:
        temp = combined_financials[ticker]
        ticker_stats = []
        for stat in stats:
            ticker_stats.append(temp.loc[stat])
        all_stats['{}'.format(ticker)] = ticker_stats
    except:
        print("can't read data for ", ticker)

all_stats_df = pd.DataFrame(all_stats, index=indx)

# cleansing of fundamental data imported in dataframe
all_stats_df.iloc[1, :] = [x.replace("M", "E+03") for x in all_stats_df.iloc[1, :].values]
all_stats_df.iloc[1, :] = [x.replace("B", "E+06") for x in all_stats_df.iloc[1, :].values]
all_stats_df.iloc[1, :] = [x.replace("T", "E+09") for x in all_stats_df.iloc[1, :].values]
all_stats_df.iloc[-1, :] = [str(x).replace("%", "E-02") for x in all_stats_df.iloc[-1, :].values]
all_stats_df[tickers] = all_stats_df[tickers].replace({',': ''}, regex=True)
for ticker in all_stats_df.columns:
    all_stats_df[ticker] = pd.to_numeric(all_stats_df[ticker].values, errors='coerce')

# calculating relevant financial metrics for each stock
transpose_df = all_stats_df.transpose()
final_stats_df = pd.DataFrame()
final_stats_df["EBIT"] = transpose_df["EBIT"]
final_stats_df["TEV"] = transpose_df["MarketCap"].fillna(0) \
                        + transpose_df["TotDebt"].fillna(0) \
                        + transpose_df["PrefStock"].fillna(0) \
                        + transpose_df["MinInterest"].fillna(0) \
                        - (transpose_df["CurrAsset"].fillna(0) - transpose_df["CurrLiab"].fillna(0))
final_stats_df["EarningYield"] = final_stats_df["EBIT"] / final_stats_df["TEV"]
final_stats_df["FCFYield"] = (transpose_df["CashFlowOps"] - transpose_df["Capex"]) / transpose_df["MarketCap"]
final_stats_df["ROC"] = transpose_df["EBIT"] / (
            transpose_df["PPE"] + transpose_df["CurrAsset"] - transpose_df["CurrLiab"])
final_stats_df["BookToMkt"] = transpose_df["BookValue"] / transpose_df["MarketCap"]
final_stats_df["DivYield"] = transpose_df["DivYield"]

################################Output Dataframes##############################

# finding value stocks based on Magic Formula
final_stats_val_df = final_stats_df.loc[tickers, :]
final_stats_val_df["CombRank"] = final_stats_val_df["EarningYield"].rank(ascending=False, na_option='bottom') + \
                                 final_stats_val_df["ROC"].rank(ascending=False, na_option='bottom')
final_stats_val_df["MagicFormulaRank"] = final_stats_val_df["CombRank"].rank(method='first')
value_stocks = final_stats_val_df.sort_values("MagicFormulaRank").iloc[:, [2, 4, 8]]
print("------------------------------------------------")
print("Value stocks based on Greenblatt's Magic Formula")
print(value_stocks)

# finding highest dividend yield stocks
high_dividend_stocks = final_stats_df.sort_values("DivYield", ascending=False).iloc[:, 6]
print("------------------------------------------------")
print("Highest dividend paying stocks")
print(high_dividend_stocks)

# # Magic Formula & Dividend yield combined
final_stats_df["CombRank"] = final_stats_df["EarningYield"].rank(ascending=False, method='first') \
                             + final_stats_df["ROC"].rank(ascending=False, method='first') \
                             + final_stats_df["DivYield"].rank(ascending=False, method='first')
final_stats_df["CombinedRank"] = final_stats_df["CombRank"].rank(method='first')
value_high_div_stocks = final_stats_df.sort_values("CombinedRank").iloc[:, [2, 4, 6, 8]]
print("------------------------------------------------")
print("Magic Formula and Dividend Yield combined")
print(value_high_div_stocks)
