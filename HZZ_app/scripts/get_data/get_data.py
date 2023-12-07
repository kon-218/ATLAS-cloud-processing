from scripts import infofile, constants
import awkward as ak
import requests
import pickle
import time
import os
import pika
import shutil

def get_data_from_files():
    data = {} # define empty dictionary to hold awkward arrays
    for s in constants.samples: # loop over samples
        print('Processing '+s+' samples') # print which sample
        frames = [] # define empty list to hold data
        for val in constants.samples[s]['list']: # loop over each file
            if s == 'data': prefix = "Data/" # Data prefix
            else: # MC prefix
                prefix = "MC/mc_"+str(infofile.infos[val]["DSID"])+"."
            fileString = constants.tuple_path+prefix+val+".4lep.root" # file name to open
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

def connect_to_rabbitmq(host, retries=5, delay=5):
    for i in range(retries):
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(host=host))
        except pika.exceptions.AMQPConnectionError:
            print(f"Failed to connect, retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Failed to connect to RabbitMQ")

# Setup pika connection
connection = connect_to_rabbitmq('rabbitmq')
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

# Delete data.pkl if it exists
if os.path.exists("data/data.pkl"):
    os.remove("data/data.pkl")

# Delete data.pkl if it exists
if os.path.exists("data/exit_code.txt"):
    os.remove("data/exit_code.txt")
    
print("Geting data")

start = time.time() # time at start of whole processing
data = get_data_from_files() # process all files
elapsed = time.time() - start # time after whole processing
print(os.getcwd())
print(os.access(os.getcwd(), os.W_OK))
print("Time taken: "+str(round(elapsed,1))+"s") # print total time taken to process every file

print(os.getcwd())
print(os.access(os.getcwd(), os.W_OK))

def delete_files_in_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

os.makedirs("data",exist_ok=True)
delete_files_in_directory('data')
    

exit_code = 0
# Write the exit code to a file
with open('data/exit_code.txt', 'w') as f:
    print("writing exit code")
    f.write(str(exit_code))

connection.close()
print("Exit 0")
