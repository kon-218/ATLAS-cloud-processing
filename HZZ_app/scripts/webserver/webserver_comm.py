from scripts.utils import connect_to_rabbitmq
import subprocess

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

#run webserver
def start_jupyter_server():
    subprocess.Popen(["jupyter", "notebook", "scripts/webserver/output.ipynb","--no-browser", "--port=8888"])

print("please open localhost:8888")
start_jupyter_server()