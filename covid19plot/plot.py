# imports and configs

from datetime import datetime, date
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import world_bank_data as wb


def simpleplot(data):
    df = data.df

    gbl = df.groupby(['Date'],as_index=False).agg(data.aggregation)

    cdn = df.loc[df['Country/Region'] == 'Canada']
    cdn = cdn.groupby(['Country/Region','Date'],as_index=False).agg(data.aggregation)

    usa = df.loc[df['Country/Region'] == 'US']
    usa = usa.groupby(['Country/Region','Date'],as_index=False).agg(data.aggregation)

    DATA = [{'n':'Global', 'df':gbl},
            {'n':'US',     'df':usa},
            {'n':'Canada', 'df':cdn}]

    fig, axs = plt.subplots(2, len(DATA))

    i=0
    for d in DATA:
        p = d['df']
        
        #print(d['n'])
        #print(p)
        
        ax = axs[0][i]
        ax.set_title(d['n'])
        for col in data.numericalbase:
            p.plot(kind='line',x='Date',y=col, color=data.numericalcolors[col], ax=ax)

        ax = axs[1][i]
        ax.set_yscale('log')
        ax.set_title("%s (log)" % d['n'])
        for col in data.numericalbase:
            p.plot(kind='line',x='Date',y=col, color=data.numericalcolors[col], ax=ax)

        i = i+1

    return fig


def countryplot(data, countries):
    df = data.df

    fig, axs = plt.subplots(3, len(countries))

    i = 0
    for country in countries:
        p = df.loc[df['Country/Region'] == country]
        p = p.groupby(['Country/Region','Date'],as_index=False).agg(data.aggregation)

        ax = axs[0][i]
        ax.set_title(country)
        for col in data.numericalbase:
            p.plot(kind='line',x='Date',y=col, color=data.numericalcolors[col], ax=ax)


        ax = axs[1][i]
        ax.set_yscale('log')
        ax.set_title("%s (log)" % country)
        for col in data.numericalbase:
            p.plot(kind='line',x='Date',y=col, color=data.numericalcolors[col], ax=ax)

        ax = axs[2][i]
        ax.set_title("%s (delta)" % country)
        for col in data.numericalbase:
            if col == "Active":
                continue
            p.plot(kind='line',x='Date',y="%sIncrease"%col, color=data.numericalcolors[col], ax=ax)

        i = i + 1

    return fig


def countryregionplot(data, country, regions):
    df = data.df
    cdf = df.loc[df['Country/Region'] == country]

    fig, axs = plt.subplots(3, len(regions))

    i = 0
    for region in regions:
        d = cdf.loc[df['Province/State'] == region]
        p = d.groupby(['Province/State','Date'],as_index=False).agg(data.aggregation)

        #print(p)
        try:
            ax = axs[0][i]
            ax.set_title(region)
            for col in data.numericalbase:
                p.plot(kind='line',x='Date',y=col, color=data.numericalcolors[col], ax=ax)

            ax = axs[1][i]
            ax.set_yscale('log')
            ax.set_title("%s (log)" % region)
            for col in data.numericalbase:
                p.plot(kind='line',x='Date',y=col, color=data.numericalcolors[col], ax=ax)

            ax = axs[2][i]
            ax.set_title("%s (delta)" % region)
            for col in data.numericalbase:
                if col == "Active":
                    continue
                p.plot(kind='line',x='Date',y="%sIncrease"%col, color=data.numericalcolors[col], ax=ax)

            i = i + 1

        except Exception as err:
            pass

    return fig


def sinceplot(data, fig=None, ax=None,
        logScale = False, startCountingAfter = 1, startCountingAfter1M = True,
        nameUnfocusedCountries = False, legendOnSide = False):

    df = data.df

    # we will get the population of each country from this data set...
    pop = wb.get_series('SP.POP.TOTL', mrv=1).reset_index()
    #print(pop['Country'].unique())
    # some countries in the pop database have different names
    popnames = {'US':'United States',
               'Korea, South':'Korea, Rep.',
               'Russia':'Russian Federation'}

    # countries we want to show in colour...
    focus = ['Canada','US','China','Korea, South','United Kingdom','Poland','Mexico','Italy','Spain','France','Germany','Russia','Japan','Belgium','Norway','Austria','Australia','Sweden','Denmark','Singapore','Malaysia','Switzerland','Finland','Portugal']
    #focus = ['Canada','US']

    # aggregate data...
    pc = ['Country/Region', 'Province/State', 'Date', 'Confirmed', 'ConfirmedIncrease', 'Deaths', 'DeathsIncrease', 'Recovered', 'RecoveredIncrease', 'Active', 'ActiveIncrease']
    d = df[pc]
    d = d.groupby(['Country/Region','Date'],as_index=False).agg(data.aggregation)

    # these are all the countries...
    countries = d['Country/Region'].unique()
    countries = focus


    # create a plot...
    if not fig or not ax:
        fig, ax = plt.subplots(1,1)

    if logScale:
        xlim = [-1,60]
        ylim = [1,5000]
        ax.set_yscale('log')
        showDoublingAtY = ylim[1] * (3/4)
    else:
        xlim = [-1,50]
        ylim = [0,1700]
        showDoublingAtY = ylim[1] - 100

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # helper
    def label_location(c):
        pre = c.tail(5).head(1)
        px = int(pre['Since'])
        py = float(pre['ConfPer1M'])

        end = c.tail(1)
        x = int(end['Since'])
        y = float(end['ConfPer1M'])
        
        dx = x-px    # days
        dy = y-py    # increase
        sl = dy/dx   # increase/days
        
        x2 = py / sl # days to double

        #print("%-20s - %u, %f, %f" % (cn,ex,ey,x2))
        if x <= xlim[1] and y <= ylim[1]:
            return (x, y, y, x2)
        
        # make it fit in the plot
        end = c[ (c['Since'] < xlim[1]) & (c['ConfPer1M'] < ylim[1]) ].tail(1)
        ex = int(end['Since'])
        ey = float(end['ConfPer1M'])
        return (ex, ey, y, x2)

    # start plotting...
    for cn in countries:
        #print("--- %s ---" % cn)
        
        # figure out how many people live in the country
        pn = cn
        if cn in popnames.keys():
            pn = popnames[cn]
        
        num = 0
        try:
            num = int(pop[pop['Country'] == pn]['SP.POP.TOTL'])
        except Exception as err:
            if cn in focus:
                print(cn,err)
            pass
        
        # skip countries with low populations
        if num < 1000000:
            continue
                
        try:
            c = d[d['Country/Region'] == cn].copy()
            c['ConfPer1M'] = c['Confirmed'] * 1000000 / num
            
            if startCountingAfter1M:
                idx = c[c['ConfPer1M'].ge(startCountingAfter)].index[0]
            else:
                idx = c[c['Confirmed'].ge(startCountingAfter)].index[0]
                
            s = c.loc[idx]['Date']
            c['Since'] = c['Date'] - s
            c['Since'] = c['Since']/np.timedelta64(1,'D')
            c = c[c['Since'] > -10]
            
            if cn in focus:
                linewidth=1
                textweight='normal'
                if cn in ['Canada','US']:
                    linewidth=2
                    textweight='bold'
                    
                c.plot(kind='line',x='Since',y='ConfPer1M', label=cn, linewidth=linewidth, legend=legendOnSide, ax=ax)
                
                (ex,ey,v,x2) = label_location(c)
                ax.text(ex, ey, cn, va='bottom', fontweight=textweight)
                ax.text(ex, ey, "(%u, %.2f)"%(v,x2), va='top', fontweight=textweight, alpha=0.5)
                
            else:
                c.plot(kind='line',x='Since',y='ConfPer1M', legend=False, color='gray', alpha=0.2, ax=ax)

                if nameUnfocusedCountries:
                    (ex,ey,v,x2) = label_location(c)
                    ax.text(ex, ey, cn, alpha=0.2)
                
        except Exception as err:
            print(cn,err)
            if cn == "Angola":
                pass
            raise err
            #pass

    if showDoublingAtY:
        def double_daily(base, arr):
            arr = np.asarray(arr)
            result = np.power(base,arr)
            return result
        for doublein in [1,2,3,4,5,6,7,8,10,12,15,20]:
            base = np.power(2,1/doublein)
            x = np.linspace(0,60)
            y = double_daily(base,x)
            plt.plot(x,y,color='red',alpha=0.25,linestyle=':')
            y = showDoublingAtY
            x = math.log(y, base)
            s = "%u day%s" % (doublein, "s" if doublein>1 else "")
            if x > xlim[1]:
                x = xlim[1]
                y = np.power(base,x)
            plt.text(x, y, s, color='red', alpha=0.5)
            if doublein == 1:
                plt.text(x, y, "double in ", color='red', alpha=0.5, ha='right')

    if startCountingAfter1M:
        ax.set_xlabel("Days since %u confirmed cases / 1M population" % startCountingAfter)
    else:
        ax.set_xlabel("Days since %u confirmed cases" % startCountingAfter)
    ax.set_ylabel("Confirmed cases per 1M population")

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    return fig

