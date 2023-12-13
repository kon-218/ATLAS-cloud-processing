# ATLAS-cloud-processing
Processing ATLAS public data using docker swarm

Please run the test and initialisation script upon initialisation to ensure that all prerequesites are met

Prerequesites:
- Docker, Docker-compose
- Python

Docker images can be built using ```docker-compose build```
These can then be ran on a host machine using ```docker-compose up```

The docker-compose file contains most configurations to do with the docker stack and should be changed as required. 
The Program requires access to multiple ports, as well as a directory on the host machine, defined using the ```volumes``` argument to map to HZZ_app in container

## Distribution across nodes

The code is setup to be distributed across a swarm using docker swarm mode

Ensure your docker engine is in swarm mode, this can be done by running the command 
```docker swarm init```

Once swarm mode is initialised, workers (VM or other computers) can be added using ```docker swarm join $token``` where the token is provided to the leader (initial machine)

To deploy the application and begin processing 

```docker stack deploy mystack --compose-file=docker-compose.yml```

The docker-compose file dictates the number of worker replicas spawned

The scripts/utils.py file contains parameters controlling how much data is sampled, it is not necessary to rebuild the docker images when changing these settings

## Communication management and results output

Communication is managed by the RabbitMQ message broker service, with the configuration panel accessible from http://0.0.0.0:15672

Results are output using a webserver, which can be found at http://0.0.0.0:8889/data/output.html, alternatively, it is available as a html file and png plot file in the data directory
