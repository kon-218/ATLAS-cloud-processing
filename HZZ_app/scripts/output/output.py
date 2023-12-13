import matplotlib.pyplot as plt
import numpy as np
import awkward as ak
from matplotlib.ticker import AutoMinorLocator # for minor ticks
import pickle
import time 
import os
import sys
from scripts import utils
import pika
import json 

state = {
    'dataDict': {sample: [] for sample in utils.samples},
    'dataRecv': 0,
    'dataExp': sum(len(category['list']) for category in utils.samples.values())
}

def plot_data(data):

    xmin = 80 * utils.GeV
    xmax = 250 * utils.GeV
    step_size = 5 * utils.GeV

    bin_edges = np.arange(start=xmin, # The interval includes this value
                    stop=xmax+step_size, # The interval doesn't include this value
                    step=step_size ) # Spacing between values
    bin_centres = np.arange(start=xmin+step_size/2, # The interval includes this value
                            stop=xmax+step_size/2, # The interval doesn't include this value
                            step=step_size ) # Spacing between values

    for output in data:
        print(output)

    data_x,_ = np.histogram(ak.to_numpy(data['data']['mllll']), 
                            bins=bin_edges ) # histogram the data
    data_x_errors = np.sqrt( data_x ) # statistical error on the data

    signal_x = ak.to_numpy(data[r'Signal ($m_H$ = 125 GeV)']['mllll']) # histogram the signal
    signal_weights = ak.to_numpy(data[r'Signal ($m_H$ = 125 GeV)'].totalWeight) # get the weights of the signal events
    signal_color = utils.samples[r'Signal ($m_H$ = 125 GeV)']['color'] # get the colour for the signal bar

    mc_x = [] # define list to hold the Monte Carlo histogram entries
    mc_weights = [] # define list to hold the Monte Carlo weights
    mc_colors = [] # define list to hold the colors of the Monte Carlo bars
    mc_labels = [] # define list to hold the legend labels of the Monte Carlo bars

    for s in utils.samples: # loop over samples
        if s not in ['data', r'Signal ($m_H$ = 125 GeV)']: # if not data nor signal
            mc_x.append( ak.to_numpy(data[s]['mllll']) ) # append to the list of Monte Carlo histogram entries
            mc_weights.append( ak.to_numpy(data[s].totalWeight) ) # append to the list of Monte Carlo weights
            mc_colors.append( utils.samples[s]['color'] ) # append to the list of Monte Carlo bar colors
            mc_labels.append( s ) # append to the list of Monte Carlo legend labels
    

    # *************
    # Main plot 
    # *************
    main_axes = plt.gca() # get current axes
    
    # plot the data points
    main_axes.errorbar(x=bin_centres, y=data_x, yerr=data_x_errors,
                    fmt='ko', # 'k' means black and 'o' is for circles 
                    label='Data') 
    
    # plot the Monte Carlo bars
    mc_heights = main_axes.hist(mc_x, bins=bin_edges, 
                                weights=mc_weights, stacked=True, 
                                color=mc_colors, label=mc_labels )
    
    mc_x_tot = mc_heights[0][-1] # stacked background MC y-axis value
    
    # calculate MC statistical uncertainty: sqrt(sum w^2)
    mc_x_err = np.sqrt(np.histogram(np.hstack(mc_x), bins=bin_edges, weights=np.hstack(mc_weights)**2)[0])
    
    # plot the signal bar
    main_axes.hist(signal_x, bins=bin_edges, bottom=mc_x_tot, 
                weights=signal_weights, color=signal_color,
                label=r'Signal ($m_H$ = 125 GeV)')
    
    # plot the statistical uncertainty
    main_axes.bar(bin_centres, # x
                2*mc_x_err, # heights
                alpha=0.5, # half transparency
                bottom=mc_x_tot-mc_x_err, color='none', 
                hatch="////", width=step_size, label='Stat. Unc.' )

    # set the x-limit of the main axes
    main_axes.set_xlim( left=xmin, right=xmax ) 
    
    # separation of x axis minor ticks
    main_axes.xaxis.set_minor_locator( AutoMinorLocator() ) 
    
    # set the axis tick parameters for the main axes
    main_axes.tick_params(which='both', # ticks on both x and y axes
                        direction='in', # Put ticks inside and outside the axes
                        top=True, # draw ticks on the top axis
                        right=True ) # draw ticks on right axis
    
    # x-axis label
    main_axes.set_xlabel(r'4-lepton invariant mass $\mathrm{m_{4l}}$ [GeV]',
                        fontsize=13, x=1, horizontalalignment='right' )
    
    # write y-axis label for main axes
    main_axes.set_ylabel('Events / '+str(step_size)+' GeV',
                        y=1, horizontalalignment='right') 
    
    # set y-axis limits for main axes
    main_axes.set_ylim( bottom=0, top=np.amax(data_x)*1.6 )
    
    # add minor ticks on y-axis for main axes
    main_axes.yaxis.set_minor_locator( AutoMinorLocator() ) 

    # Add text 'ATLAS Open Data' on plot
    plt.text(0.05, # x
            0.93, # y
            'ATLAS Open Data', # text
            transform=main_axes.transAxes, # coordinate system used is that of main_axes
            fontsize=13 ) 
    
    # Add text 'for education' on plot
    plt.text(0.05, # x
            0.88, # y
            'for education', # text
            transform=main_axes.transAxes, # coordinate system used is that of main_axes
            style='italic',
            fontsize=8 ) 
    
    # Add energy and luminosity
    lumi_used = str(utils.lumi*utils.fraction) # luminosity to write on the plot
    plt.text(0.05, # x
            0.82, # y
            '$\sqrt{s}$=13 TeV,$\int$L dt = '+lumi_used+' fb$^{-1}$', # text
            transform=main_axes.transAxes ) # coordinate system used is that of main_axes
    
    # Add a label for the analysis carried out
    plt.text(0.05, # x
            0.76, # y
            r'$H \rightarrow ZZ^* \rightarrow 4\ell$', # text 
            transform=main_axes.transAxes ) # coordinate system used is that of main_axes

    # draw the legend
    main_axes.legend( frameon=False ) # no box around the legend

    os.makedirs('data/static', exist_ok=True)
    plt.savefig('data/static/plot.png')

    return

def callback(ch,method,properties,body):

    # Extract name and data
    data = json.loads(body)
    name = data.get("data_name", None)
    data = ak.from_iter(data.get("data", None))
    
    # Add to dictionary
    # Add data to dictionary
    for category, s in utils.samples.items():
        if name in s['list']:
            data_dict_key = category
            state['dataDict'][data_dict_key].append(data)  # Append data to the list

    
    state['dataRecv'] += 1
    print(" [x] Received %r", name)
    Recv_channel.basic_ack(delivery_tag=method.delivery_tag)

    print(state['dataDict'])

    if state['dataRecv'] == state['dataExp']:
        Recv_channel.stop_consuming() 


# Setup pika connection
connection = utils.connect_to_rabbitmq('rabbitmq')
Recv_channel = connection.channel()

# Declare the queue
Recv_channel.queue_declare(queue='done_queue',durable=True)

# Consume messages from the queue
Recv_channel.basic_consume('done_queue', callback, auto_ack=False)

Recv_channel.start_consuming()

# Concatenate full data into plottable dict
for sample, data in state['dataDict'].items():
    state['dataDict'][sample] = ak.concatenate(data)

plot_data(state['dataDict'])

Send_channel = connection.channel()
Send_channel.queue_declare(queue='webserver_queue', durable=True)
Send_channel.basic_publish(exchange='',routing_key='webserver_queue', body='done', properties=pika.BasicProperties(delivery_mode=2,))
Send_channel.close()