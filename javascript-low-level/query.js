'use strict';
/*
* Copyright IBM Corp All Rights Reserved
*
* SPDX-License-Identifier: Apache-2.0
*/
/*
 * Chaincode query
 */

var Fabric_Client = require('fabric-client');
var fs = require('fs');
var path = require('path');

var network_path = path.resolve('..', '..', 'ben-multi-host');
var org1tlscacert_path = path.resolve(network_path, 'crypto-config', 'peerOrganizations', 'org1.example.com', 'tlsca', 'tlsca.org1.example.com-cert.pem');
var org1tlscacert = fs.readFileSync(org1tlscacert_path, 'utf8');

var org2tlscacert_path = path.resolve(network_path, 'crypto-config', 'peerOrganizations', 'org2.example.com', 'tlsca', 'tlsca.org2.example.com-cert.pem');
var org2tlscacert = fs.readFileSync(org2tlscacert_path, 'utf8');

var org3tlscacert_path = path.resolve(network_path, 'crypto-config', 'peerOrganizations', 'org3.example.com', 'tlsca', 'tlsca.org3.example.com-cert.pem');
var org3tlscacert = fs.readFileSync(org3tlscacert_path, 'utf8');

//
var fabric_client = new Fabric_Client();

// setup the fabric network
var channel = fabric_client.newChannel('mychannel');
var peer = fabric_client.newPeer('grpcs://localhost:7051', {
	'ssl-target-name-override': 'peer0.org1.example.com',
	pem: org1tlscacert
});
var peer2 = fabric_client.newPeer('grpcs://10.21.4.11:7051', {
	'ssl-target-name-override': 'peer0.org2.example.com',
	pem: org2tlscacert
});
var peer3 = fabric_client.newPeer('grpcs://10.21.1.22:7051', {
	'ssl-target-name-override': 'peer0.org3.example.com',
	pem: org3tlscacert
});
channel.addPeer(peer);
channel.addPeer(peer2);
channel.addPeer(peer3);

//
var store_path = path.join(__dirname, 'hfc-key-store');
console.log('Store path:'+store_path);

// create the key value store as defined in the fabric-client/config/default.json 'key-value-store' setting
Fabric_Client.newDefaultKeyValueStore({ path: store_path
}).then((state_store) => {
	// assign the store to the fabric client
	fabric_client.setStateStore(state_store);
	var crypto_suite = Fabric_Client.newCryptoSuite();
	// use the same location for the state store (where the users' certificate are kept)
	// and the crypto store (where the users' keys are kept)
	var crypto_store = Fabric_Client.newCryptoKeyStore({path: store_path});
	crypto_suite.setCryptoKeyStore(crypto_store);
	fabric_client.setCryptoSuite(crypto_suite);

	// get the enrolled user from persistence, this user will sign all requests
	return fabric_client.getUserContext('user1', true);
}).then((user_from_store) => {
	if (user_from_store && user_from_store.isEnrolled()) {
		console.log('Successfully loaded user1 from persistence');
	} else {
		throw new Error('Failed to get user1.... run registerUser.js');
	}

	// queryCar chaincode function - requires 1 argument, ex: args: ['CAR4'],
	// queryAllCars chaincode function - requires no arguments , ex: args: [''],
	const request = {
		//targets : --- letting this default to the peers assigned to the channel
		chaincodeId: 'fabcar',
		fcn: 'queryCar',
		args: ['CAR0']
	};

	// send the query proposal to the peer
	return channel.queryByChaincode(request);
}).then((query_responses) => {
	console.log("Query has completed, checking results");
	console.log(query_responses)
	// query_responses could have more than one  results if there multiple peers were used as targets
	if (query_responses && query_responses.length == 3) {
		if (query_responses[0] instanceof Error) {
			console.error("error from query = ", query_responses[0]);
		} else {
			console.log("Response 1 is ", query_responses[0].toString());
			console.log('\n')
			console.log("Response 1 is ", query_responses[1].toString());
			console.log('\n')
			console.log("Response 1 is ", query_responses[2].toString());
			console.log('\n')
		}
	} else {
		console.log("No payloads were returned from query");
	}
}).catch((err) => {
	console.error('Failed to query successfully :: ' + err);
});
