from web3 import Web3
from dotenv import load_dotenv
from vyper import compile_code
import os

load_dotenv()

RPC_URL = os.getenv("RPC_URL")


def main():
    print("Let's read in the Vyper code and deploy it to the blockchain!")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    # Configure web3 for Hedera
    w3.eth.default_block = "latest"
    
    with open("favorites.vy", "r") as favorites_file:
        favorites_code = favorites_file.read()
        compliation_details = compile_code(
            favorites_code, output_formats=["bytecode", "abi"]
        )

    chain_id = 296  # Hedera Testnet chain ID

    print("Getting environment variables...")
    my_address = os.getenv("MY_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")
    account_id = os.getenv("ACCOUNT_ID")

    # Convert Hedera address to EVM address format
    if len(my_address) > 42:  # If it's a long Hedera format address
        raw_address = my_address[-40:]
    else:
        raw_address = my_address.lower()
        if raw_address.startswith("0x"):
            raw_address = raw_address[2:]

    # Convert to checksum address
    my_address = Web3.to_checksum_address("0x" + raw_address)

    print(f"Using address: {my_address}")
    print(f"Account ID: {account_id}")

    try:
        # Check balance before deployment
        balance = w3.eth.get_balance(my_address)
        balance_in_hbar = w3.from_wei(balance, "ether")
        print(f"Account balance: {balance_in_hbar} HBAR")

        if balance == 0:
            print("Your account has no HBAR! Please get some testnet HBAR from the faucet:")
            print("1. Go to https://portal.hedera.com/")
            print("2. Create an account if you haven't already")
            print("3. Your testnet account should automatically have HBAR")
            print("4. Your address:", my_address)
            return

        # Create the contract in Python
        favorites_contract = w3.eth.contract(
            abi=compliation_details["abi"], bytecode=compliation_details["bytecode"]
        )

        # Get the nonce
        nonce = w3.eth.get_transaction_count(my_address)
        gas_price = w3.eth.gas_price

        print("Building the transaction...")
        transaction = favorites_contract.constructor().build_transaction({
            "chainId": chain_id,
            "nonce": nonce,
            "gas": 3000000,
            "gasPrice": gas_price,
            "from": my_address
        })

        print("Signing transaction...")
        signed_txn = w3.eth.account.sign_transaction(
            transaction,
            private_key=private_key
        )

        print("Deploying contract...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print("Waiting for transaction to be mined...")
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Contract deployed! Address: {tx_receipt.contractAddress}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your Hedera credentials and network connection.")
        print("Debug info:")
        print(f"RPC URL: {RPC_URL}")
        print(f"Chain ID: {chain_id}")
        print(f"Address: {my_address}")
        print(f"Account ID: {account_id}")


if __name__ == "__main__":
    main()
