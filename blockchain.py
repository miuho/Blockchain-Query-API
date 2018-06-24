# blockchain.py
# Parse and evaluate blocks of Bitcoin blockchain
#
# HingOn Miu

# https://bitcoin.org/en/developer-reference#block-headers
# https://en.bitcoin.it/wiki/Block_hashing_algorithm
# https://en.bitcoin.it/wiki/Block

import os
import sys
import io
import random
import string
import json
import time
import struct
import binascii
import hashlib


# previous block hash of genesis block of bitcoin blockchain
source_hash = "0000000000000000000000000000000000000000000000000000000000000000"

# previous block header hash (little endian) to block
# prev_hash -> block
prev_hash_to_blocks = {}

# current block header hash (little endian) to previous block header hash (little endian)
# curr_hash -> prev_hash -> block
curr_hash_to_prev_hash = {}

# total number of blocks
block_count = 0

# number of blocks in longest chain
blockchain_height = 0

# block hash of latest block (little endian)
latest_block_little = ""

# transaction hash (little endian) to previous block header hash (little endian)
# txid -> prev_hash -> block
txid_to_prev_hash = {}


# input transaction of a transaction
class InputTransaction:

	def __init__(self, prev_tx_hash, script, seq_num):
		# txid of the transaction holding the output to spend
		# 32 bytes little endian
		self.prev_tx_hash = prev_tx_hash
		# script that satisfies the conditions placed in the outpoint's pubkey script
		# variable length hex string
		self.script = script
		# sequence number
		# 4 bytes little endian
		self.seq_num = seq_num

	def get_prev_hash_little(self):
		return self.prev_tx_hash

	def get_prev_hash_big(self):
		# convert to binary
		hash_bin = self.prev_tx_hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def get_script_little(self):
		return self.script

	def get_script_big(self):
		return self.script.decode('hex')[::-1].encode('hex_codec')

	def get_seq_int(self):
		return int(self.seq_num.decode('hex')[::-1].encode('hex_codec'), 16)


# output transaction of a transaction
class OutputTransaction:

	def __init__(self, satoshi_amount, script):
		# amount of satoshis to spend
		# 8 bytes little endian
		self.satoshi_amount = satoshi_amount
		# script that satisfies the conditions placed in the outpoint's pubkey script
		# variable length hex string
		self.script = script

	def get_satoshi_int(self):
		return int(self.satoshi_amount.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_script_little(self):
		return self.script

	def get_script_big(self):
		return self.script.decode('hex')[::-1].encode('hex_codec')


# Each transaction in a block
class Transaction:

	def __init__(self, tx_hash, ver_num, input_tx_count, input_txs, output_tx_count, output_txs, locktime):
		# txid of the transaction
		# 32 bytes little endian
		self.hash = tx_hash
		# transaction version number
		# 4 bytes little endian
		self.version = ver_num
		# number of input transactions of a transaction
		# variable length integer
		self.input_tx_count = input_tx_count
		# list of input transactions (InputTransaction)
		self.input_txs = input_txs
		# number of output transactions of a transaction
		# variable length integer
		self.output_tx_count = output_tx_count
		# list of output transactions (OutputTransaction)
		self.output_txs = output_txs
		# time (Unix epoch time) or block number
		# 4 bytes little endian
		self.locktime = locktime

	def get_hash_little(self):
		return self.hash

	def get_hash_big(self):
		# convert to binary
		hash_bin = self.hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def get_version_int(self):
		return int(self.version.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_input_count_int(self):
		return self.input_tx_count

	def get_inputs(self):
		return self.input_txs

	def get_output_count_int(self):
		return self.output_tx_count

	def get_outputs(self):
		return self.output_txs

	def get_locktime_int(self):
		return int(self.locktime.decode('hex')[::-1].encode('hex_codec'), 16)


# Each block in blockchain
class Block:

	def __init__(self, ver_num, prev_hash, merk_hash, start_time, nBits, nonce, tx_count, txs):
		# block version number indicates which set of block validation rules to follow
		# 4 bytes little endian
		self.version = ver_num
		# SHA256(SHA256()) hash in internal byte order of the previous block's header
		# 32 bytes little endian
		self.previous_block_header_hash = prev_hash
		# SHA256(SHA256()) hash in internal byte order
		# merkle root is derived from hashes of all transactions included in this block,
		# ensuring none of the transactions can be modified without modifying the header
		# 32 bytes little endian
		self.merkle_root_hash = merk_hash
		# block time is a Unix epoch time when the miner started hashing the header
		# Must be strictly greater than the median time of the previous 11 blocks
		# 4 bytes little endian
		self.start_time = start_time
		# target threshold this block's header hash must be less than or equal to
		# 4 bytes little endian
		self.nBits = nBits
		# arbitrary number miners change to modify the header hash in order to produce a
		# hash less than or equal to the target threshold
		# 4 bytes little endian
		self.nonce = nonce
		# indicator of whether this block is in the longest blockchain
		self.main_chain = False
		# blockchain height of this block
		self.height = 0
		# number of transactions in this block
		self.tx_count = tx_count
		# list of transactions (Transaction)
		self.txs = txs

	def get_transactions(self):
		return self.txs

	def get_tx_count_int(self):
		return self.tx_count

	def get_version_int(self):
		return int(self.version.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_time_int(self):
		return int(self.start_time.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_nBits_int(self):
		return int(self.nBits.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_nonce_int(self):
		return int(self.nonce.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_merk_hash_little(self):
		return self.merkle_root_hash

	def get_merk_hash_big(self):
		# convert to binary
		hash_bin = self.merkle_root_hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def set_main_chain(self):
		self.main_chain = True
		return

	def get_main_chain(self):
		return self.main_chain

	def set_height(self, height):
		self.height = height
		return

	def get_height(self):
		return self.height

	def get_prev_hash_little(self):
		return self.previous_block_header_hash

	def get_prev_hash_big(self):
		# convert to binary
		hash_bin = self.previous_block_header_hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def get_curr_hash_little(self):
		# header in little-endian hex
		header_hex = (self.version + self.previous_block_header_hash + self.merkle_root_hash + 
			self.start_time + self.nBits + self.nonce)

		# convert to binary
		header_bin = header_hex.decode('hex')

		# SHA256(SHA256(header))
		header_hash = hashlib.sha256(hashlib.sha256(header_bin).digest()).digest()

		# little-endian hash
		hash_little = header_hash.encode('hex_codec')

		return hash_little

	def get_curr_hash_big(self):
		# header in little-endian hex
		header_hex = (self.version + self.previous_block_header_hash + self.merkle_root_hash + 
			self.start_time + self.nBits + self.nonce)

		# convert to binary
		header_bin = header_hex.decode('hex')

		# SHA256(SHA256(header))
		header_hash = hashlib.sha256(hashlib.sha256(header_bin).digest()).digest()

		# big-endian hash
		hash_big = header_hash[::-1].encode('hex_codec')

		return hash_big


def get_merkle_root(child_hashes):
	# recursively compute merkle hashes
	if len(child_hashes) == 1:
		# return only merkle root 
		return child_hashes[0]
	else:
		# bottom-up merkle hashing from children
		parent_hashes = []

		# pad the hashes with last hash if length is odd
		if len(child_hashes) % 2 == 1:
			child_hashes += [child_hashes[len(child_hashes) - 1]]

		# number of pairs of children
		num_pair = len(child_hashes) / 2

		# compute parent hash for each children pair hashes
		for i in range(0, num_pair):
			child_1 = child_hashes[i * 2]
			child_2 = child_hashes[i * 2 + 1]

			# convert to binary data
			child_1_bin = child_1.decode('hex')
			child_2_bin = child_2.decode('hex')

			# SHA256(SHA256(hash | hash))
			parent_bin = hashlib.sha256(hashlib.sha256(child_1_bin + child_2_bin).digest()).digest()

			# little-endian hash
			parent = parent_bin.encode('hex_codec')

			parent_hashes += [parent]

		# get merkle root of parents
		return get_merkle_root(parent_hashes)


def parse_var_len_int(block, nth_byte):
	# variable length integer: 1, 3, 5, or 9 bytes
	num_byte_parsed = 0
	data = 0

	# parse first byte
	first_byte = struct.unpack("<B", block[nth_byte: nth_byte + 1])[0]
	if first_byte < 0xFD:
		data = first_byte
		num_byte_parsed = 1

	elif first_byte == 0xFD:
		data = struct.unpack("<H", block[nth_byte + 1: nth_byte + 3])[0]
		num_byte_parsed = 3

	elif first_byte == 0xFE:
		data = struct.unpack("<I", block[nth_byte + 1: nth_byte + 5])[0]
		num_byte_parsed = 5

	elif first_byte == 0xFF:
		data = struct.unpack("<Q", block[nth_byte + 1: nth_byte + 9])[0]
		num_byte_parsed = 9

	else:
		# should not get here
		return 0, 0

	return data, num_byte_parsed


def byte_to_hex_string_little(bytes):
	# hex string little endian
	return  binascii.hexlify(bytes)


def byte_to_hex_string_big(bytes):
	# hex string big endian
	return  binascii.hexlify(bytes[::-1])


def parse_block(block, nth_byte):
	# magic number 0xD9B4BEF9
	# 4 bytes little endian to hex big endian
	magic_num = byte_to_hex_string_big(block[nth_byte: nth_byte + 4])
	#print (magic_num)
	# make sure block parsed correctly
	assert (magic_num == b'd9b4bef9')
	nth_byte += 4

	# block size
	# 4 bytes little endian to int
	block_size = struct.unpack("<I", block[nth_byte: nth_byte + 4])[0]
	#print block_size
	nth_byte += 4
	# start index of the block
	start_block_byte = nth_byte

	# version number
	ver_num = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
	#print ver_num
	nth_byte += 4

	# previous block's header hash
	prev_hash = byte_to_hex_string_little(block[nth_byte: nth_byte + 32])
	#print prev_hash
	nth_byte += 32

	# merkle root hash
	merk_hash = byte_to_hex_string_little(block[nth_byte: nth_byte + 32])
	#print merk_hash
	nth_byte += 32

	# Unix epoch time
	start_time = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
	#print start_time
	nth_byte += 4

	# target difficulty threshold
	nBits = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
	#print nBits
	nth_byte += 4

	# arbitrary number to match difficulty
	nonce = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
	#print nonce
	nth_byte += 4

	# transaction count
	tx_count, num_byte_parsed = parse_var_len_int(block, nth_byte)
	nth_byte += num_byte_parsed
	#print(tx_count)

	# list of all transaction hashes
	tx_hashes = []
	# list of all transactions
	transactions = []

	# parse each transaction
	for i in range(0, tx_count):
		# start index of transaction
		start_tx_byte = nth_byte
		# raw transaction data concatenated to compute txid
		raw_tx_data = ""

		# transaction version number
		tx_ver_num = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
		raw_tx_data += tx_ver_num
		nth_byte += 4

		# input transaction count
		input_tx_count, num_byte_parsed = parse_var_len_int(block, nth_byte)
		raw_tx_data += byte_to_hex_string_little(block[nth_byte: nth_byte + num_byte_parsed])
		nth_byte += num_byte_parsed

		# list of all input transactions
		input_transactions = []

		# parse each input transaction
		for j in range(0, input_tx_count):
			# txid of the transaction holding the output to spend
			prev_tx_hash = byte_to_hex_string_little(block[nth_byte: nth_byte + 32])
			raw_tx_data += prev_tx_hash
			nth_byte += 32

			# output index number of the specific output to spend from the transaction
			prev_tx_index = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
			raw_tx_data += prev_tx_index
			nth_byte += 4

			# script size
			script_size, num_byte_parsed = parse_var_len_int(block, nth_byte)
			raw_tx_data += byte_to_hex_string_little(block[nth_byte: nth_byte + num_byte_parsed])
			nth_byte += num_byte_parsed

			# script that satisfies the conditions placed in the outpoint's pubkey script
			script = byte_to_hex_string_little(block[nth_byte: nth_byte + script_size])
			raw_tx_data += byte_to_hex_string_little(block[nth_byte: nth_byte + script_size])
			nth_byte += script_size

			# sequence number
			seq_num = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
			raw_tx_data += seq_num
			nth_byte += 4

			# new input transaction
			input_tx = InputTransaction(prev_tx_hash, script, seq_num)
			input_transactions += [input_tx]

		# output transaction count
		output_tx_count, num_byte_parsed = parse_var_len_int(block, nth_byte)
		raw_tx_data += byte_to_hex_string_little(block[nth_byte: nth_byte + num_byte_parsed])
		nth_byte += num_byte_parsed

		# list of all output transactions
		output_transactions = []

		# parse each output transaction
		for j in range(0, output_tx_count):
			# amount of satoshis to spend
			satoshi_amount = byte_to_hex_string_little(block[nth_byte: nth_byte + 8])
			raw_tx_data += satoshi_amount
			nth_byte += 8

			# script size
			script_size, num_byte_parsed = parse_var_len_int(block, nth_byte)
			raw_tx_data += byte_to_hex_string_little(block[nth_byte: nth_byte + num_byte_parsed])
			nth_byte += num_byte_parsed

			# script that satisfies the conditions placed in the outpoint's pubkey script
			script = byte_to_hex_string_little(block[nth_byte: nth_byte + script_size])
			raw_tx_data += byte_to_hex_string_little(block[nth_byte: nth_byte + script_size])
			nth_byte += script_size

			# new output transaction
			output_tx = OutputTransaction(satoshi_amount, script)
			output_transactions += [output_tx]

		# time (Unix epoch time) or block number
		locktime = byte_to_hex_string_little(block[nth_byte: nth_byte + 4])
		raw_tx_data += locktime
		nth_byte += 4

		# number of bytes of this raw transaction
		tx_size = (start_tx_byte - nth_byte)

		# convert to binary
		raw_tx_data_bin = raw_tx_data.decode('hex')

		# SHA256(SHA256(raw transaction))
		tx_hash = hashlib.sha256(hashlib.sha256(raw_tx_data_bin).digest()).digest()

		# little-endian hash
		tx_hash_little = tx_hash.encode('hex_codec')
		#print(tx_hash_little)
		tx_hashes += [tx_hash_little]

		# each transaction hash is unique txid
		# txid -> prev_hash of block header
		txid_to_prev_hash[tx_hash_little] = prev_hash

		# new transaction
		tx = Transaction(tx_hash_little, tx_ver_num, input_tx_count, input_transactions,
						output_tx_count, output_transactions, locktime)
		transactions += [tx]

	# make sure the bytes transactions and header are parsed correctly
	assert (nth_byte - start_block_byte == block_size)

	# compute the Merkle root of all transactions
	merk_root_of_txs = get_merkle_root(tx_hashes)

	# verify the merkle root hash in block header
	assert (merk_hash == merk_root_of_txs)

	# create block
	block = Block(ver_num, prev_hash, merk_hash, start_time, nBits, nonce, tx_count, transactions)

	# prev_hash -> curr header
	if prev_hash in prev_hash_to_blocks:
		# another chain of blocks
		prev_hash_to_blocks[prev_hash].append(block)
	else:
		prev_hash_to_blocks[prev_hash] = [block]

	# curr_hash -> prev_hash
	curr_hash_to_prev_hash[block.get_curr_hash_little()] = prev_hash

	return block_size


def load_file(filename):
	global block_count

	header_start = 0

	# open .dat file to load blocks
	with open(filename, "rb") as file:
		data = file.read()
		# get the file size
		file_end = os.stat(filename).st_size
		
		# parse every block
		while True:
			block_size = parse_block(data, header_start)

			# track total block parsed
			block_count += 1

			# size(magic_num) + block_size + size(null padding)
			header_start += (4 + block_size + 4)

			# check if file ends
			# size(magic_num) + size(blocksize) + size(header)
			if (header_start + (4 + 4 + 80)) >= file_end:
				break

	file.close()
	return


def get_filename(directory_path, nth_file):
	# left padd zero strings
	nth_file_string = str(nth_file).zfill(5)

	return directory_path + "blk" + nth_file_string + ".dat"


def load_blockchain(directory_path):
	nth_file = 0
	# load all .dat files in given directory path
	filename = get_filename(directory_path, nth_file)

	# load every file
	while os.path.isfile(filename):
		load_file(filename)

		print ("Parsed " + filename)

		# parse next file
		nth_file += 1
		filename = get_filename(directory_path, nth_file)

	return


def compute_distances_bfs():
	# start from source vertex
	queue = [source_hash]
	# mark all vertices not visited
	distances = {source_hash: 0}
	# track the longest distance to source
	max_distance = -1
	max_hash = ""

	# traverse all vertices
	while len(queue) != 0:
		# remove and return first element in list
		curr_hash = queue.pop(0)

		# skip vertex with no outgoing neighbor
		if curr_hash not in prev_hash_to_blocks:
			continue

		# get all outgoing neighbors
		blocks = prev_hash_to_blocks[curr_hash]

		# traverse outgoing neighbors
		for block in blocks:
			# compute header hash
			next_hash = block.get_curr_hash_little()

			# add to stack if not visited
			if next_hash not in distances:
				# insert element to end of list
				queue.append(next_hash)

				# compute distance to source
				distances[next_hash] = distances[curr_hash] + 1
				block.set_height(distances[next_hash] - 1)

				# record longest chain
				if distances[next_hash] > max_distance:
					max_distance = distances[next_hash]
					max_hash = next_hash

	return max_hash, max_distance - 1


def setup(directory_path):
	global blockchain_height
	global latest_block_little

	# load all blocks
	print("Load blockchain files...")
	load_blockchain(directory_path)

	# breath first search to compute each vertex distance to source
	print("Compute BFS distances from genesis block...")
	longest_hash, longest_chain_height = compute_distances_bfs()
	#print("Main Chain Height: " + str(longest_chain_height))
	blockchain_height = longest_chain_height
	latest_block_little = longest_hash

	# get latest block hash
	latest_block = latest_block_little.decode('hex')[::-1].encode('hex_codec')
	#print("Latest Block Hash: " + latest_block)
	
	curr_hash = longest_hash
	prev_hash = curr_hash_to_prev_hash[longest_hash]
	# flag main chain blocks from the longest latest block to genesis block
	while prev_hash != source_hash:
		# get current block
		blocks = prev_hash_to_blocks[prev_hash]
		for block in blocks:
			# set main chain flag
			if block.get_curr_hash_little() == curr_hash:
				#print(curr_hash)
				block.set_main_chain()
				break
		
		# flag previous block
		curr_hash = prev_hash
		prev_hash = curr_hash_to_prev_hash[prev_hash]

	# get genesis block
	blocks = prev_hash_to_blocks[source_hash]
	# set main chain flag
	blocks[0].set_main_chain()
	
	return


def get_block_header(block_hash_big):
	# convert to little endian
	block_hash_little = block_hash_big.decode('hex')[::-1].encode('hex_codec')

	# check if block hash exists
	if block_hash_little not in curr_hash_to_prev_hash:
		return -1, "", "", -1, -1, -1

	# previous block hash
	prev_hash = curr_hash_to_prev_hash[block_hash_little]
	blocks = prev_hash_to_blocks[prev_hash]
	# get block
	for block in blocks:
		if block.get_curr_hash_little() == block_hash_little:

			# get header fields
			ver_num = block.get_version_int()
			prev_hash = block.get_prev_hash_big()
			merk_hash = block.get_merk_hash_big()
			start_time = block.get_time_int()
			nBits = block.get_nBits_int()
			nonce = block.get_nonce_int()

			return ver_num, prev_hash, merk_hash, start_time, nBits, nonce

	return -1, "", "", -1, -1, -1


def get_block_height(block_hash_big):
	# convert to little endian
	block_hash_little = block_hash_big.decode('hex')[::-1].encode('hex_codec')

	# check if block hash exists
	if block_hash_little not in curr_hash_to_prev_hash:
		return -1

	# previous block hash
	prev_hash = curr_hash_to_prev_hash[block_hash_little]
	blocks = prev_hash_to_blocks[prev_hash]
	# get block
	for block in blocks:
		if block.get_curr_hash_little() == block_hash_little:

			return block.get_height()

	return -1


def get_main_chain(block_hash_big):
	# convert to little endian
	block_hash_little = block_hash_big.decode('hex')[::-1].encode('hex_codec')

	# check if block hash exists
	if block_hash_little not in curr_hash_to_prev_hash:
		return False

	# previous block hash
	prev_hash = curr_hash_to_prev_hash[block_hash_little]
	blocks = prev_hash_to_blocks[prev_hash]
	# get block
	for block in blocks:
		if block.get_curr_hash_little() == block_hash_little:

			return block.get_main_chain()

	return False


def get_latest_block():
	# get latest block hash big endian
	latest_block = latest_block_little.decode('hex')[::-1].encode('hex_codec')

	return latest_block


def get_latest_height():
	return blockchain_height


def get_block_transactions(block_hash_big):
	# convert to little endian
	block_hash_little = block_hash_big.decode('hex')[::-1].encode('hex_codec')

	# check if block hash exists
	if block_hash_little not in curr_hash_to_prev_hash:
		return -1, []

	# previous block hash
	prev_hash = curr_hash_to_prev_hash[block_hash_little]
	blocks = prev_hash_to_blocks[prev_hash]

	# get block
	for block in blocks:
		if block.get_curr_hash_little() == block_hash_little:

			# number of transactions in this block
			count = block.get_tx_count_int()
			# list of transactions (Transaction)
			txs = block.get_transactions()

			parsed_txs = []
			# traverse all transactions
			for i in range(0, count):
				tx = txs[i]

				# txid of the transaction
				txid = tx.get_hash_big()

				# number of output transactions
				output_count = tx.get_output_count_int()
				# list of output transactions (OutputTransaction)
				output_txs = tx.get_outputs()

				btc_amount = 0.0
				# traverse all output transactions
				for j in range(0, output_count):
					output_tx = output_txs[j]

					# 100000000 satoshi = 1 BTC
					satoshi = output_tx.get_satoshi_int()
					btc_amount += (satoshi / 100000000.0)

				parsed_txs += [(txid, btc_amount)]
			
			return count, parsed_txs

	return -1, []


def get_transaction_info(tx_hash_big):
	# convert to little endian
	tx_hash_little = tx_hash_big.decode('hex')[::-1].encode('hex_codec')

	# check if tx hash exists
	if tx_hash_little not in txid_to_prev_hash:
		return "", -1, -1, -1, 0.0, -1 

	# previous block hash
	prev_hash = txid_to_prev_hash[tx_hash_little]
	blocks = prev_hash_to_blocks[prev_hash]

	# get block
	for block in blocks:
		# number of transactions in this block
		count = block.get_tx_count_int()
		# list of transactions (Transaction)
		txs = block.get_transactions()

		# traverse all transactions
		for i in range(0, count):
			tx = txs[i]

			if tx.get_hash_little() == tx_hash_little:
				# transaction version number
				ver = tx.get_version_int()

				# number of input transactions
				input_count = tx.get_input_count_int()

				# number of output transactions
				output_count = tx.get_output_count_int()

				# list of output transactions (OutputTransaction)
				output_txs = tx.get_outputs()

				btc_amount = 0.0
				# traverse all output transactions
				for j in range(0, output_count):
					output_tx = output_txs[j]

					# 100000000 satoshi = 1 BTC
					satoshi = output_tx.get_satoshi_int()
					btc_amount += (satoshi / 100000000.0)

				# lock time
				locktime = tx.get_locktime_int()

				return block.get_curr_hash_big(), ver, input_count, output_count, btc_amount, locktime

	return "", -1, -1, -1, 0.0, -1


def get_transaction_inputs(tx_hash_big):
	# convert to little endian
	tx_hash_little = tx_hash_big.decode('hex')[::-1].encode('hex_codec')

	# check if tx hash exists
	if tx_hash_little not in txid_to_prev_hash:
		return -1, []

	# previous block hash
	prev_hash = txid_to_prev_hash[tx_hash_little]
	blocks = prev_hash_to_blocks[prev_hash]

	# get block
	for block in blocks:
		# number of transactions in this block
		count = block.get_tx_count_int()
		# list of transactions (Transaction)
		txs = block.get_transactions()

		# traverse all transactions
		for i in range(0, count):
			tx = txs[i]

			if tx.get_hash_little() == tx_hash_little:
				# number of input transactions
				input_count = tx.get_input_count_int()

				# list of input transactions (InputTransaction)
				input_txs = tx.get_inputs()

				parsed_input_txs = []
				# traverse all input transactions
				for j in range(0, input_count):
					input_tx = input_txs[j]

					prev_txid = input_tx.get_prev_hash_big()
					script = input_tx.get_script_big()
					seq = input_tx.get_seq_int()

					parsed_input_txs += [(prev_txid, script, seq)]

				return input_count, parsed_input_txs

	return -1, []


def get_transaction_outputs(tx_hash_big):
	# convert to little endian
	tx_hash_little = tx_hash_big.decode('hex')[::-1].encode('hex_codec')

	# check if tx hash exists
	if tx_hash_little not in txid_to_prev_hash:
		return -1, []

	# previous block hash
	prev_hash = txid_to_prev_hash[tx_hash_little]
	blocks = prev_hash_to_blocks[prev_hash]

	# get block
	for block in blocks:
		# number of transactions in this block
		count = block.get_tx_count_int()
		# list of transactions (Transaction)
		txs = block.get_transactions()

		# traverse all transactions
		for i in range(0, count):
			tx = txs[i]

			if tx.get_hash_little() == tx_hash_little:
				# number of output transactions
				output_count = tx.get_output_count_int()

				# list of output transactions (OutputTransaction)
				output_txs = tx.get_outputs()

				parsed_output_txs = []
				# traverse all output transactions
				for j in range(0, output_count):
					output_tx = output_txs[j]

					# 100000000 satoshi = 1 BTC
					satoshi = output_tx.get_satoshi_int()
					script = output_tx.get_script_big()

					parsed_output_txs += [(satoshi / 100000000.0, script)]

				return output_count, parsed_output_txs

	return -1, []



