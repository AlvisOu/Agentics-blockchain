import os
from web3 import Web3
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# --- Web3 setup ---
RPC_URL = os.getenv("RPC_URL")  # e.g., Infura/Alchemy endpoint
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # For signing transactions
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
with open("RentalAgreement.abi", "r") as f:
    CONTRACT_ABI = f.read()

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

mcp = FastMCP("SmartContract")

@mcp.tool()
def pay_deposit() -> dict:
    """Pay the security deposit to the contract."""
    try:
        tx = contract.functions.payDeposit().build_transaction({
            "from": account.address,
            "value": contract.functions.securityDeposit().call(),
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return {"tx_hash": tx_hash.hex()}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def pay_rent(month: int) -> dict:
    """Pay rent for a specific month."""
    try:
        tx = contract.functions.payRent(month).build_transaction({
            "from": account.address,
            "value": contract.functions.monthlyRent().call(),
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return {"tx_hash": tx_hash.hex()}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def confirm_rent(month: int) -> dict:
    """Confirm rent payment for a specific month."""
    try:
        tx = contract.functions.confirmRent(month).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return {"tx_hash": tx_hash.hex()}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def transfer_address(new_landlord: str) -> dict:
    """Transfer landlord address to a new address."""
    try:
        tx = contract.functions.transferAddress(Web3.to_checksum_address(new_landlord)).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return {"tx_hash": tx_hash.hex()}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def contract_status() -> dict:
    """Get the current status of the contract."""
    try:
        return {
            "landlord": contract.functions.landlord().call(),
            "tenant": contract.functions.tenant().call(),
            "monthlyRent": contract.functions.monthlyRent().call(),
            "securityDeposit": contract.functions.securityDeposit().call(),
            "leaseStart": contract.functions.leaseStart().call(),
            "propertyAddress": contract.functions.propertyAddress().call(),
            "depositPaid": contract.functions.depositPaid().call(),
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting Smart Contract MCP Server...")
    mcp.run(transport="stdio")