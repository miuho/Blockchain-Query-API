# Bitcoin Blockchain Query API

Implementation of REST API Bitcoin Blockchain Query service.

HingOn Miu


Steps:
- Run install.sh to install Python dependencies and Bitcoin core.

- Run Bitcoin full node to download complete raw .dat blockchain files.

- Run server.py to listen for HTTP connections on port 9000.

- Enter URL in browser or use curl to send HTTP GET requests.

URL Example:
http://127.0.0.1:9000/blockheight?
000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f


Documentation:
	Base URL: "http://127.0.0.1:9000"
	Method: GET

	Block Header API
		Request block header of the block.

		Endpoint: "/blockheader"

		Parameters:
			$block_hash: 256bit hash of block header

		Full URL:
			http://[HOST]:[PORT]/blockheader?[BLOCK_HASH]

		Success Response:
			200 OK, application/json

		{
			"version":     <block version number>,
			"prev_block":  <hash of previous block header>,
			"mrkl_root":   <hash of all transactions in the block>,
			"time":        <time when miner started hashing header>,
			"bits":        <target threshold for block hash>,
			"nonce":       <arbitrary number to modify block hash>
		}

	Block Transactions API
		Request all transactions of the block.

		Endpoint: "/blocktransactions"

		Parameters:
			$block_hash: 256bit hash of block header

		Full URL:
			http://[HOST]:[PORT]/blocktransactions?[BLOCK_HASH]

		Success Response:
			200 OK, application/json

		{
			"tx_count":  <number of transactions>,
			"transactions":
			[ {
				"tx_hash": <256bit hash of transaction>
				"value":   <BTC amount of transaction>
			}, ... ]
		}

	Block Height API
		Request block height of the block.

		Endpoint: "/blockheight"

		Parameters:
			$block_hash: 256bit hash of block header

		Full URL:
			http://[HOST]:[PORT]/blockheight?[BLOCK_HASH]

		Success Response:
			200 OK, application/json

		{
			"height":  <Number of blocks since genesis block>
		}

	Main Chain API
		Verify the block is in the longest chain.

		Endpoint: "/mainchain"

		Parameters:
			$block_hash: 256bit hash of block header

		Full URL:
			http://[HOST]:[PORT]/mainchain?[BLOCK_HASH]

		Success Response:
			200 OK, application/json

		{
			"main_chain":  <true/false>
		}

	Latest Block API
		Request latest block hash in the longest chain.

		Endpoint: "/latestblock"

		Parameters:
			NONE

		Full URL:
			http://[HOST]:[PORT]/latestblock

		Success Response:
			200 OK, application/json

		{
			"hash":  <Latest block hash in main chain>
		}

	Latest Height API
		Request current block height in the longest chain.

		Endpoint: "/latestheight"

		Parameters:
			NONE

		Full URL:
			http://[HOST]:[PORT]/latestheight

		Success Response:
			200 OK, application/json

		{
			"height":  <Block height of main chain>
		}

	Transaction Information API
		Request information of the transaction.

		Endpoint: "/transactioninfo"

		Parameters:
			$tx_hash: 256bit hash of transaction

		Full URL:
			http://[HOST]:[PORT]/transactioninfo?[TX_HASH]

		Success Response:
			200 OK, application/json

		{
			"block_hash":      <256bit hash of block header>
			"version":         <transaction version number>
			"input_tx_count":  <number of input transactions>
			"output_tx_count": <number of output transactions>
			"value":           <BTC amount of transaction>
			"lock_time":       <lock time>
		}

	Transaction Inputs API
		Request input transactions of the transaction.

		Endpoint: "/transactioninputs"

		Parameters:
			$tx_hash: 256bit hash of transaction

		Full URL:
			http://[HOST]:[PORT]/transactioninputs?[TX_HASH]

		Success Response:
			200 OK, application/json

		{
			"input_tx_count":  <number of input transactions>,
			"input_transactions":
			[ {
				"prev_hash":    <256bit hash of previous transaction>
				"sig_script":   <pubkey signature script>
				"seq_num":      <sequence number>
			}, ... ]
		}

	Transaction Outputs API
		Request output transactions of the transaction.

		Endpoint: "/transactionoutputs"

		Parameters:
			$tx_hash: 256bit hash of transaction

		Full URL:
			http://[HOST]:[PORT]/transactionoutputs?[TX_HASH]

		Success Response:
			200 OK, application/json

		{
			"output_tx_count":  <number of output transactions>,
			"output_transactions":
			[ {
				"value":       <BTC amount of output transaction>
				"sig_script":  <pubkey signature script>
			}, ... ]
		}



