# imports and configs

from datetime import datetime, date
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import world_bank_data as wb


def countryplot(data, countries, showIncrease=False):
    df = data.df

    rows = 2 + (1 if showIncrease else 0);

    fig, axs = plt.subplots(rows, len(countries))

    i = 0
    for country in countries:
        if country == 'Global':
            p = df.groupby(['Date'],as_index=False).agg(data.aggregation)
        else:
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

        if showIncrease:
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
        logScale = False, dataColumn='Confirmed',
        startCountingAfter = 1, startCountingAfter1M = True,
        nameUnfocusedCountries = False, legendOnSide = False):

    df = data.df

    if not dataColumn in data.numericalbase:
        raise "cannot plot %s" % dataColumn

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
    #countries = focus

    # create a plot...
    if not fig or not ax:
        fig, ax = plt.subplots(1,1)

    if logScale:
        if dataColumn == 'Confirmed':   # log confirmed
            xlim = [-1,70]
            ylim = [1,6000]
        else:                           # log deaths
            xlim = [-1,60]
            ylim = [1,700]
        ax.set_yscale('log')
        showDoublingAtY = ylim[1] * (3/4)
        doubleindays=[1,2,3,4,5,6,7,8,10,12,15,20]
    else:
        if dataColumn == 'Confirmed':   # linear confirmed
            xlim = [0,70]
            ylim = [0,3500]
        else:                           # deaths confirmed
            xlim = [0,60]
            ylim = [0,350]
        showDoublingAtY = ylim[1] - 100
        doubleindays=[1,2,3,4,5,6,7,8]

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # helper, returns (x,y,lastValue,daysToDouble), for country label
    def build_label_data(c):
        pre = c.tail(2).head(1)
        px = int(pre['Since'])
        py = float(pre['Per1M'])

        end = c.tail(1)
        x = int(end['Since'])
        y = float(end['Per1M'])

        if logScale:
            dx = x-px    # days
            dy = y-py    # increase
            sl = dy/dx   # increase/days
            
            rt = y / sl  # days to double
            rtl = "dtd"  # describe "rt"

        else:
            dx = x-px    # days
            dy = y-py    # increase
            sl = dy / dx # increase/day

            rt = sl
            rtl = "Δ"    # describe "rt"

        #print("%-20s - x=%u..%u (%u), y=%.3f..%.3f (%.3f), sl=%.3f, %s=%.3f"
        #        % (cn,px,x,dx,py,y,dy,sl,rtl,rt))

        if x <= xlim[1] and y <= ylim[1]:
            return (x, y, y, rt, rtl)
        
        # make it fit in the plot
        end = c[ (c['Since'] < xlim[1]) & (c['Per1M'] < ylim[1]) ].tail(1)
        ex = int(end['Since'])
        ey = float(end['Per1M'])
        return (ex, ey, y, rt, rtl)

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
            c['Per1M'] = c[dataColumn] * 1000000 / num
            
            if startCountingAfter1M:
                idx = c[c['Per1M'].ge(startCountingAfter)].index[0]
            else:
                idx = c[c[dataColumn].ge(startCountingAfter)].index[0]
                
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
                    
                c.plot(kind='line',x='Since',y='Per1M', label=cn, linewidth=linewidth, legend=legendOnSide, ax=ax)
                
                (ex,ey,v,rt,rtl) = build_label_data(c)
                ax.text(ex, ey, cn, va='bottom', fontweight=textweight)
                ax.text(ex, ey, "(%u, %s=%.2f)"%(v,rtl,rt), va='top', fontweight=textweight, alpha=0.5)
                
            else:
                c.plot(kind='line',x='Since',y='Per1M', legend=False, color='gray', alpha=0.2, ax=ax)

                if nameUnfocusedCountries:
                    (ex,ey,v,rt,rtl) = build_label_data(c)
                    ax.text(ex, ey, cn, alpha=0.2)
                
        except Exception as err:
            #print(cn,err)
            if cn == "Angola":
                pass
            #raise err
            pass

    if showDoublingAtY:
        def double_daily(base, arr):
            arr = np.asarray(arr)
            result = np.power(base,arr)
            return result
        for doublein in doubleindays:
            base = np.power(2,1/doublein)
            x = np.linspace(0,xlim[1])
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

    if dataColumn == 'Confirmed':
        dataDesc = 'Confirmed cases'
    else:
        dataDesc = dataColumn

    ax.set_title("%s per population, since %u observed %s"
            % (dataDesc, startCountingAfter, "(logarithmic)" if logScale else ""),
            fontsize=20)

    if startCountingAfter1M:
        ax.set_xlabel("Days since %u %s / 1M population" % (startCountingAfter, dataDesc))
    else:
        ax.set_xlabel("Days since %u %s" % (startCountingAfter, dataDesc))

    ax.set_ylabel("%s per 1M population" % dataDesc)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    caption = "%s @ %s (%s)" % (data.giturl, data.gitdate, data.githash)
    ax.text(0.5, -0.05, caption, size=8, ha="center", transform=ax.transAxes)

    return fig

