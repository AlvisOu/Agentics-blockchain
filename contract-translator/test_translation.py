from contract_to_solidity_llm import ContractToSolidityTranslator

contract_text = """
Simple Rental Agreement

This agreement is between Jane Smith (landlord) and John Doe (tenant).
The tenant agrees to pay 2 ETH for rent at 123 Main Street.
Security deposit is 4 ETH.
Lease starts February 1, 2025.
"""

with open('contracts/test_contract.txt', 'w') as f:
    f.write(contract_text)

translator = ContractToSolidityTranslator()
result = translator.translate_contract(
    input_path='contracts/test_contract.txt',
    output_dir='./output'
)

print("✓ Translation complete!")
print(f"Check ./output/ for your files")