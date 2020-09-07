#!/bin/bash

# mynode2
scp -r crypto-config channel-artifacts node4@mynode2:/home/node4/Build-Multi-Host-Network-Hyperledger

# mynode
scp -r crypto-config channel-artifacts ben@mynode3:/home/ben/Build-Multi-Host-Network-Hyperledger

