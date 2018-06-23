# server.py
# Run http server for Bitcoin blockchain Query API
#
# HingOn Miu

# https://docs.python.org/3/library/http.server.html

import io
import random
import string
import json
import time
import socket
import threading
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse
import blockchain


# sample http GET url for blockchain query request
# http://127.0.0.1:9000/blockheight?000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
# http://127.0.0.1:9000/blockheader?0000000082b5015589a3fdf2d4baff403e6f0be035a5d9742c1cae6295464449
# http://127.0.0.1:9000/latestheight

# API endpoint to get block height of the block
blockheight_endpoint = "/blockheight"
# API endpoint to check if block is in main chain
mainchain_endpoint = "/mainchain"
# API endpoint to get block header of the block
blockheader_endpoint = "/blockheader"
# API endpoint to get latest block
latestblock_endpoint = "/latestblock"
# API endpoint to get latest block height
latestheight_endpoint = "/latestheight"
# API endpoint to get transactions of the block
blocktransactions_endpoint = "/blocktransactions"
# API endpoint to get information of the transaction
transactioninfo_endpoint = "/transactioninfo"
# API endpoint to get input transactions of the transaction
transactioninputs_endpoint = "/transactioninputs"
# API endpoint to get output transactions of the transaction
transactionoutputs_endpoint = "/transactionoutputs"

API_endpoints = {
					blockheight_endpoint, mainchain_endpoint,
					blockheader_endpoint, latestblock_endpoint,
					latestheight_endpoint, blocktransactions_endpoint,
					transactioninfo_endpoint, transactioninputs_endpoint,
					transactionoutputs_endpoint
				}


class Handler(BaseHTTPRequestHandler):
	# handle http GET requests
	def do_GET(self):
		print("GET: " + self.path)

		# parse url path
		parsed_path = urlparse(self.path)

		# check if API endpoint correct
		endpoint = parsed_path.path
		if endpoint not in API_endpoints:
			self.send_error(404)
			return

		# parse query
		hash_big_endian = parsed_path.query

		# check if hash has proper format
		if (endpoint == blockheight_endpoint or 
			endpoint == mainchain_endpoint or
			endpoint == blockheader_endpoint or
			endpoint == blocktransactions_endpoint or
			endpoint == transactioninfo_endpoint or
			endpoint == transactioninputs_endpoint or
			endpoint == transactionoutputs_endpoint):

			# check if string length is 64
			if len(hash_big_endian) != 64:
				self.send_error(400)
				return

			# check if it is proper hex string
			try:
				int(hash_big_endian, 16)
			except ValueError:
				self.send_error(400)
				return

		else:
			# other endpoints do not have parameter
			if hash_big_endian != "":
				self.send_error(400)
				return


		if endpoint == blockheight_endpoint:
			# get block height
			blockheight = blockchain.get_block_height(hash_big_endian)

			# check if block hash is invalid
			if blockheight == -1:
				message = json.dumps({"error": "Invalid Block Hash"})
			else:
				message = json.dumps({"height": blockheight})

		elif endpoint == mainchain_endpoint:
			# check if block is in main chain (longest blockchain)
			mainchain = blockchain.get_main_chain(hash_big_endian)

			message = json.dumps({"main_chain": mainchain})

		elif endpoint == blockheader_endpoint:
			# get block header fields
			ver_num, prev_hash, merk_hash, start_time, nBits, nonce = \
				blockchain.get_block_header(hash_big_endian)

			# check if block hash is invalid
			if ver_num == -1:
				message = json.dumps({"error": "Invalid Block Hash"})
			else:
				message = json.dumps({"version": ver_num, "prev_block": prev_hash,
									"mrkl_root": merk_hash, "time": start_time, 
									"bits": nBits, "nonce": nonce})

		elif endpoint == latestblock_endpoint:
			# get the latest block of main chain
			latestblock = blockchain.get_latest_block()

			message = json.dumps({"hash": latestblock})

		elif endpoint == latestheight_endpoint:
			# get the latest block height of main chain
			latestheight = blockchain.get_latest_height()

			message = json.dumps({"height": latestheight})

		elif endpoint == blocktransactions_endpoint:
			# get block transactions
			count, transactions = blockchain.get_block_transactions(hash_big_endian)

			# check if block hash is invalid
			if count == -1:
				message = json.dumps({"error": "Invalid Block Hash"})
			else:
				txs = []
				# traverse all transactions
				for i in range(0, count):
					txid, btc_amount = transactions[i]
					txs += [{"tx_hash": txid, "value": btc_amount}]

				message = json.dumps({"tx_count": count, "transactions": txs})

		elif endpoint == transactioninfo_endpoint:
			# get transaction info
			block_hash, ver, input_count, output_count, btc_amount, locktime  = \
				blockchain.get_transaction_info(hash_big_endian)

			# check if tx hash is invalid
			if ver == -1:
				message = json.dumps({"error": "Invalid Transaction Hash"})
			else:
				message = json.dumps({"block_hash": block_hash, "version": ver,
									"input_tx_count": input_count,
									"output_tx_count": output_count,
									"value": btc_amount, "lock_time": locktime})

		elif endpoint == transactioninputs_endpoint:
			# get input transactions
			count, input_transactions  = blockchain.get_transaction_inputs(hash_big_endian)

			# check if tx hash is invalid
			if count == -1:
				message = json.dumps({"error": "Invalid Transaction Hash"})
			else:
				input_txs = []
				# traverse all input transactions
				for i in range(0, count):
					prev_txid, script, seq = input_transactions[i]
					input_txs += [{"prev_hash": prev_txid, "sig_script": script, "seq_num": seq}]

				message = json.dumps({"input_tx_count": count, "input_transactions": input_txs})

		elif endpoint == transactionoutputs_endpoint:
			# get output transactions
			count, output_transactions  = blockchain.get_transaction_outputs(hash_big_endian)

			# check if tx hash is invalid
			if count == -1:
				message = json.dumps({"error": "Invalid Transaction Hash"})
			else:
				output_txs = []
				# traverse all input transactions
				for i in range(0, count):
					satoshi, script = output_transactions[i]
					output_txs += [{"value": satoshi, "sig_script": script}]

				message = json.dumps({"output_tx_count": count, "output_transactions": output_txs})

		else:
			# should not get here
			message = json.dumps({"error": "Invalid Request"})

		self.send_response(200)
		self.send_header("Content-Type", "text/plain; charset=utf-8")
		self.end_headers()

		self.wfile.write(message.encode('utf-8'))
		self.wfile.write(b'\n')


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass


if __name__ == "__main__":
	HOST, PORT = "localhost", 9000
	# create server
	server = ThreadedHTTPServer((HOST, PORT), Handler)
	# start server thread to handle requests and server thread starts new thread for each new request
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = True
	server_thread.start()
	print("Server thread ready to handle http requests...")

	# parse blockchain files
	#blockchain.setup("Bitcoin/blocks/")
	blockchain.setup("")
	print("Blockchain setup done.")

	# hang to wait for connections
	while True:
		continue

	# clean up server
	server.shutdown()
	server.server_close()



