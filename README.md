# ATLAS-cloud-processing
Processing ATLAS public data using docker swarm

Please run the test and initialisation script upon initialisation to ensure that all prerequesites are met

Prerequesites:
- Docker, Docker-compose
- Python

Docker images can be built using ```docker-compose build```
These can then be ran on a host machine using ```docker-compose up```

## Distribution across nodes

The code is setup to be distributed across a swarm using docker swarm mode

Ensure your docker engine is in swarm mode, this can be done by running the command 
```docker swarm init```

Once swarm mode is initialised, workers (VM or other computers) can be added using ```docker swarm join $token``` where the token is provided to the leader (initial machine)

To deploy the application and begin processing 

```docker stack deploy mystack --compose-file=docker-compose.yml```

The docker-compose file dictates the number of worker replicas spawned

The scripts/utils.py file contains parameters controlling how much data is sampled, it is not necessary to rebuild the docker images when changing these settings
