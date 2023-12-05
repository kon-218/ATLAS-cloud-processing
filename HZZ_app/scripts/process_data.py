import time 
import uproot
import awkward as ak
import infofile as infofile
import vector
from multiprocessing import Pool
from flask import Flask, request, jsonify
import os
import constants as constants
import pika
import pickle

def read_file(ch, method, properties, body):
    global channel2
    path, sample = pickle.loads(body)
    start = time.time() # start the clock
    print("\tProcessing: "+sample) # print which sample is being processed
    data_all = [] # define empty list to hold all data for this sample
    
    # open the tree called mini using a context manager (will automatically close files/resources)
    with uproot.open(path + ":mini") as tree:
        numevents = tree.num_entries # number of event
        tasks = []
        for data in tree.iterate(['lep_pt','lep_eta','lep_phi',
                                  'lep_E','lep_charge','lep_type', 
                                  # add more variables here if you make cuts on them 
                                  'mcWeight','scaleFactor_PILEUP',
                                  'scaleFactor_ELE','scaleFactor_MUON',
                                  'scaleFactor_LepTRIGGER'], # variables to calculate Monte Carlo weight
                                 library="ak", # choose output type as awkward array
                                 entry_stop=numevents*constants.fraction): # process up to numevents*fraction
            tasks.append((data, sample))

            nIn = len(data) # number of events in this batch

        with Pool() as p:
            data_all = p.map(process_chunk,tasks)

    data = ak.concatenate(data_all) # return array containing events passing all cuts

    os.makedirs("data",exist_ok=True)
    with open(f'data/{sample}.pkl', 'wb') as f:
        pickle.dump(data, f)
        print("writing data to {}".format(f.name))

    #ch.basic_ack(delivery_tag = method.delivery_tag)
    ch.basic_ack(delivery_tag = method.delivery_tag)
    channel2.basic_publish(exchange = "",
                           routing_key='done_queue',
                           body='done',
                           properties=pika.BasicProperties(delivery_mode=2,))  # make message persistent


def process_chunk(args):
    data, sample = args
    if 'data' not in sample: xsec_weight = get_xsec_weight(sample) # get cross-section weight
    # Process the chunk and return the result
    if 'data' not in sample: # only do this for Monte Carlo simulation files
        # multiply all Monte Carlo weights and scale factors together to give total weight
        data['totalWeight'] = calc_weight(xsec_weight, data)

    # cut on lepton charge using the function cut_lep_charge defined above
    data = data[~cut_lep_charge(data.lep_charge)]

    # cut on lepton type using the function cut_lep_type defined above
    data = data[~cut_lep_type(data.lep_type)]

    # calculation of 4-lepton invariant mass using the function calc_mllll defined above
    data['mllll'] = calc_mllll(data.lep_pt, data.lep_eta, data.lep_phi, data.lep_E)

    # array contents can be printed at any stage like this
    #print(data)

    # array column can be printed at any stage like this
    #print(data['lep_pt'])

    # multiple array columns can be printed at any stage like this
    #print(data[['lep_pt','lep_eta']])
    #nOut = len(data) # number of events passing cuts in this batch
    
    return data




def calc_weight(xsec_weight, events):
    return (
        xsec_weight
        * events.mcWeight
        * events.scaleFactor_PILEUP
        * events.scaleFactor_ELE
        * events.scaleFactor_MUON 
        * events.scaleFactor_LepTRIGGER
    )

def get_xsec_weight(sample):
    info = infofile.infos[sample] # open infofile
    xsec_weight = (constants.lumi*1000*info["xsec"])/(info["sumw"]*info["red_eff"]) #*1000 to go from fb-1 to pb-1
    return xsec_weight # return cross-section weight

def calc_mllll(lep_pt, lep_eta, lep_phi, lep_E):
    # construct awkward 4-vector array
    p4 = vector.zip({"pt": lep_pt, "eta": lep_eta, "phi": lep_phi, "E": lep_E})
    # calculate invariant mass of first 4 leptons
    # [:, i] selects the i-th lepton in each event
    # .M calculates the invariant mass
    return (p4[:, 0] + p4[:, 1] + p4[:, 2] + p4[:, 3]).M * constants.MeV




# cut on lepton charge
# paper: "selecting two pairs of isolated leptons, each of which is comprised of two leptons with the same flavour and opposite charge"
def cut_lep_charge(lep_charge):
# throw away when sum of lepton charges is not equal to 0
# first lepton in each event is [:, 0], 2nd lepton is [:, 1] etc
    return lep_charge[:, 0] + lep_charge[:, 1] + lep_charge[:, 2] + lep_charge[:, 3] != 0

# cut on lepton type
# paper: "selecting two pairs of isolated leptons, each of which is comprised of two leptons with the same flavour and opposite charge"
def cut_lep_type(lep_type):
# for an electron lep_type is 11
# for a muon lep_type is 13
# throw away when none of eeee, mumumumu, eemumu
    sum_lep_type = lep_type[:, 0] + lep_type[:, 1] + lep_type[:, 2] + lep_type[:, 3]
    return (sum_lep_type != 44) & (sum_lep_type != 48) & (sum_lep_type != 52)

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
channel2 = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
channel2.queue_declare(queue='done_queue', durable=True)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=read_file)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()