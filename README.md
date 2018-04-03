#Blockchain Simulator
An implementation of a simple blockchain that can accept arbitrary binary data as input into blocks.  The simulation can be run using Docker.  

Using Docker, you can run a large number of nodes to participate in a blockchain network.  The nodes use UDP broadcast to discover eachother, and send a heartbeat out every 30 seconds to ensure the other nodes know they are still alive.  Each node will start mining empty blocks, and will add any new binary data it receives from external clients to the block if it can.  Once the block has been mined it is propagated through the network so that the other nodes can verify it and add it to their chain.

## Getting Started
A detailed getting started guide can be found at https://github.com/KyleS22/BlockchainSimulator/wiki/Quick-Start-Guide

## Documentation
Detailed documentation can be found in the project [wiki](https://github.com/KyleS22/BlockchainSimulator/wiki)

### Dependencies

This project uses Python 3.7 and Docker to simulate a scalable peer-to-peer network for the blockchain. A detailed list of python packages required for this project can be found in the [requirements.txt](https://github.com/KyleS22/BlockchainSimulator/blob/master/requirements.txt).






