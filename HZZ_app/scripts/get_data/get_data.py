from scripts import infofile, utils
import awkward as ak
import requests
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

channel.queue_declare(queue='task_queue', durable=True)
    
print("Geting data")

start = time.time() # time at start of whole processing
data = get_data_from_files() # process all files
elapsed = time.time() - start # time after whole processing
print(os.getcwd())
print(os.access(os.getcwd(), os.W_OK))
print("Time taken: "+str(round(elapsed,1))+"s") # print total time taken to process every file

print(os.getcwd())
print(os.access(os.getcwd(), os.W_OK))

os.makedirs("data",exist_ok=True)
utils.delete_files_in_directory('data')

os.makedirs("data/static",exist_ok=True)
    
connection.close()
print("Exit 0")
