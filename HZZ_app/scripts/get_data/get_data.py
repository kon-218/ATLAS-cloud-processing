from scripts import infofile, utils
import awkward as ak
import pickle
import time
import os
import pika
import shutil

def get_data_from_files():
    data = {} # define empty dictionary to hold awkward arrays
    for s in utils.samples: # loop over samples
        print('Processing '+s+' samples') # print which sample
        frames = [] # define empty list to hold data
        for val in utils.samples[s]['list']: # loop over each file
            if s == 'data': prefix = "Data/" # Data prefix
            else: # MC prefix
                prefix = "MC/mc_"+str(infofile.infos[val]["DSID"])+"."
            fileString = utils.tuple_path+prefix+val+".4lep.root" # file name to open
            data_to_send = [fileString, val]
            serialized_data = pickle.dumps(data_to_send)
            # send add filestring to queue
            channel.basic_publish(exchange='',
                                  routing_key='task_queue',
                                  body=serialized_data,
                                  properties=pika.BasicProperties(
                                      delivery_mode = 2, # make message persistent
                                  ))
            print(" [x] Sent %r" % fileString)
            #temp = read_file(fileString,val) # call the function read_file defined below
        #     frames.append(temp) # append array returned from read_file to list of awkward arrays
        # data[s] = ak.concatenate(frames) # dictionary entry is concatenated awkward arrays

    return data # return dictionary of awkward arrays

# Setup pika connection
connection = utils.connect_to_rabbitmq('rabbitmq')
channel = connection.channel()

# Declare channel
channel.queue_declare(queue='task_queue', durable=True)
    
print("Geting data")

data = get_data_from_files() # process all files

# Empty the data directory in preperation for a fresh processing run 
os.makedirs("data",exist_ok=True)
utils.delete_files_in_directory('data')

# Create static data dir for plot output 
os.makedirs("data/static",exist_ok=True)
    
# Finished communicating
connection.close()
