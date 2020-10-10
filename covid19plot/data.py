import pandas as pd
import subprocess

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def importdata():

    # --------------------------------------------------
    # load the datasets

    df_c = pd.read_csv("COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv")
    df_d = pd.read_csv("COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv")
    df_r = pd.read_csv("COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv")

    # --------------------------------------------------
    # next rotate them to add a Date column

    ids = ['Country/Region', 'Province/State', 'Lat', 'Long']
    numericalbase = ['Confirmed', 'Deaths', 'Recovered']

    df_c = df_c.melt(id_vars=ids, var_name="Date", value_name="Confirmed")
    df_d = df_d.melt(id_vars=ids, var_name="Date", value_name="Deaths")
    df_r = df_r.melt(id_vars=ids, var_name="Date", value_name="Recovered")

    # --------------------------------------------------
    # next merge the Confirmed/Deaths/Recovered into one dataframe

    # https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html
    keys = ids + ["Date"]

    df = pd.merge(df_c, df_d, how='outer', on=keys)
    df = pd.merge(df, df_r, how='outer', on=keys)
    df = df.reset_index()

    # --------------------------------------------------

    for n in numericalbase:
        df[n] = df[n].fillna(0)

    # --------------------------------------------------
    # ad an active column

    df['Active'] = df['Confirmed'] - (df['Recovered'] + df['Deaths'])

    numericalbase.append('Active')

    # --------------------------------------------------
    # some countries have no Province/State, we need empty strings

    df['Province/State'] = df['Province/State'].fillna('-')

    # --------------------------------------------------
    # finally cleanup the dates (who uses M/D/Y in a dataset ???)

    #print(df)
    #for d in df['Date']:
    #    print(d)

    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')

    # --------------------------------------------------
    # add an Id column

    df['Id'] = df['Country/Region'] + '-' + df['Province/State']

    # --------------------------------------------------
    # add Increase columns

    numericalcolors = { 'Confirmed':'blue',
                        'Deaths':   'red',
                        'Recovered':'green',
                        'Active':   'orange' }

    numerical = []
    gb = df.groupby('Id')
    for n in numericalbase:
        numerical.append(n)
            
        ni = '%sIncrease' % n
        df[ni] = gb[n].diff()
        numerical.append(ni)
        
        #na = '%sAvg' % n
        #df[na] = gb[n].apply(pd.rolling_mean, 3, min_periods=1)
        #df[na] = gb[n].transform('cumsum')
        #numericalx.append(na)
        
    # --------------------------------------------------
    # these are the columns we may want to sum later

    aggregation = {}
    for n in numerical:
        aggregation[n] = 'sum'

    # --------------------------------------------------
    # fix column order

    cols = ['Id'] + keys + numerical

    df = df[cols]

    # --------------------------------------------------
    # sort by Confirmed column

    #df = df.sort_values(by=['Date', 'Confirmed'])

    # --------------------------------------------------
    # write it for review

    df.to_csv("csse-combined.csv", index=False)

    # --------------------------------------------------
    # df dump

    #for c in df.columns:
    #    u = df[c].unique()
    #    print("%-20s %u" % (c, len(u)))

    #print(df['Country/Region'].unique())

    df = df.fillna(0)

    #df.describe(include="all")
    #df.isna().sum()
    #x = df[df['Country/Region'] == 'US']
    #print(x[x['Date'] == datetime(2020,3,30)])
    #print("--")
    #print(x[x['Date'] == datetime(2020,3,31)])

    # --------------------------------------------------
    # collect git info

    gitdir = 'COVID-19'
    
    result = subprocess.run(['git','log','-1','--pretty=format:%h'], cwd=gitdir, stdout=subprocess.PIPE)
    githash = result.stdout.decode('utf-8').strip()

    result = subprocess.run(['git','log','-1','--pretty=format:%ad','--date=short'], cwd=gitdir, stdout=subprocess.PIPE)
    gitdate = result.stdout.decode('utf-8').strip()

    result = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=gitdir, stdout=subprocess.PIPE)
    giturl = result.stdout.decode('utf-8').strip()

    # --------------------------------------------------
    # return

    ret = {
            'df':df,
            'aggregation':aggregation,
            'numerical':numerical,
            'numericalbase':numericalbase,
            'numericalcolors':numericalcolors,
            'gitdir':gitdir,
            'githash':githash,
            'gitdate':gitdate,
            'giturl':giturl,
            }

    return dotdict(ret)
