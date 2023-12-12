from scripts.utils import connect_to_rabbitmq

connection = connect_to_rabbitmq('rabbitmq')
channel = connection.channel()
channel.queue_declare("webserver_queue",durable=True)

print("Waiting for plot to be ready")

message = None
while not message:
    method_frame, header_frame, body = channel.basic_get(queue="webserver_queue", auto_ack=True)
    if method_frame:
        message = body

print("received message: %s" % message)

#run webserver (finished script)