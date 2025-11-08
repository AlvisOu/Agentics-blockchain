"""
Simple working translator - no dependencies on IBM Agentics
"""
import json
from pathlib import Path
import PyPDF2
from pydantic import BaseModel
from typing import List
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# Schemas
class ContractParty(BaseModel):
    name: str
    role: str
    address: str = None

class MonetaryAmount(BaseModel):
    amount: float
    currency: str = "ETH"
    purpose: str

class ContractDate(BaseModel):
    date_type: str
    value: str = None
    day_of_month: int = None

class PropertyDetails(BaseModel):
    address: str
    additional_info: str = None

class ContractSchema(BaseModel):
    parties: List[ContractParty]
    monetary_amounts: List[MonetaryAmount]
    dates: List[ContractDate]
    property_details: PropertyDetails
    additional_terms: List[str] = []
    contract_type: str = "rental_agreement"

class SimpleContractTranslator:
    """Working translator using direct Anthropic API"""
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env file")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        print(f"Reading PDF: {pdf_path}")
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                print(f"  Reading page {page_num}...")
                text += page.extract_text() + "\n"
            return text.strip()
    
    def parse_contract(self, contract_text: str) -> ContractSchema:
        """Parse contract using Claude"""
        print("Parsing contract with Claude...")
        
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": f"""Extract structured information from this rental contract.

CONTRACT TEXT:
{contract_text}

Return ONLY a JSON object (no markdown, no explanations) with this structure:
{{
    "parties": [{{"name": "string", "role": "landlord or tenant", "address": null}}],
    "monetary_amounts": [{{"amount": number, "currency": "ETH", "purpose": "rent or deposit or fee"}}],
    "dates": [{{"date_type": "start or end or payment_due", "value": "date string", "day_of_month": number or null}}],
    "property_details": {{"address": "string", "additional_info": null}},
    "additional_terms": [],
    "contract_type": "rental_agreement"
}}

Extract all parties, amounts, dates, and property information from the contract."""
            }]
        )
        
        response_text = message.content[0].text.strip()

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            parsed = json.loads(response_text)
            schema = ContractSchema(**parsed)
            print(f"✓ Parsed: {len(schema.parties)} parties, {len(schema.monetary_amounts)} amounts")
            return schema
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response was: {response_text[:500]}")
            raise
    
    def generate_solidity(self, schema: ContractSchema) -> str:
        """Generate Solidity from schema"""
        print("Generating Solidity code...")
        
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": f"""Generate a complete, production-ready Solidity smart contract for this rental agreement:

SCHEMA:
{schema.json(indent=2)}

Requirements:
- Use Solidity ^0.8.0
- Include constructor with parameters for landlord, tenant, rent, deposit, lease start, property address
- Add state variables for all key information
- Implement payable functions: payDeposit() and payRent(uint256 month)
- Implement landlord function: confirmRent(uint256 month)
- Add events for all state changes
- Include onlyLandlord and onlyTenant modifiers
- Add natspec comments
- Follow security best practices

Return ONLY the complete Solidity code, no explanations or markdown."""
            }]
        )
        
        code = message.content[0].text.strip()
       
        if "```solidity" in code:
            code = code.split("```solidity")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        print(f"✓ Generated {len(code.splitlines())} lines of Solidity")
        return code
    
    def generate_abi(self, solidity_code: str) -> list:
        """Generate ABI from Solidity"""
        print("Generating ABI...")
        
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": f"""Generate the complete ABI (Application Binary Interface) JSON for this Solidity contract:

{solidity_code}

Return ONLY a JSON array following the Ethereum ABI specification. Include:
- Constructor with all input parameters
- All public/external functions with inputs, outputs, and stateMutability
- All events with their parameters (mark indexed parameters)
- All public state variables (as view functions)

Return ONLY the JSON array, no explanations or markdown."""
            }]
        )
        
        abi_text = message.content[0].text.strip()

        if "```json" in abi_text:
            abi_text = abi_text.split("```json")[1].split("```")[0].strip()
        elif "```" in abi_text:
            abi_text = abi_text.split("```")[1].split("```")[0].strip()
        
        try:
            abi = json.loads(abi_text)
            print(f"✓ Generated ABI with {len(abi)} elements")
            return abi
        except Exception as e:
            print(f"Error parsing ABI JSON: {e}")
            print(f"Response was: {abi_text[:500]}")
            raise
    
    def translate_contract(self, input_path: str, output_dir: str = "./output"):
        """Complete translation pipeline"""
        
        print("\n" + "="*60)
        print("CONTRACT TO SOLIDITY TRANSLATOR")
        print("="*60)

        print("\n[Step 1/5] Reading contract file...")
        if input_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(input_path)
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
        print(f"✓ Read {len(text)} characters\n")
 
        print("[Step 2/5] Parsing contract...")
        schema = self.parse_contract(text)
        print()
 
        print("[Step 3/5] Generating Solidity...")
        solidity = self.generate_solidity(schema)
        print()
   
        print("[Step 4/5] Generating ABI...")
        abi = self.generate_abi(solidity)
        print()
        
        print("[Step 5/5] Saving files...")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        sol_file = output_path / "RentalAgreement.sol"
        with open(sol_file, 'w', encoding='utf-8') as f:
            f.write(solidity)
        print(f"  ✓ Saved: {sol_file}")
   
        abi_file = output_path / "RentalAgreement.abi.json"
        with open(abi_file, 'w', encoding='utf-8') as f:
            json.dump(abi, f, indent=2)
        print(f"  ✓ Saved: {abi_file}")

        schema_file = output_path / "contract_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema.dict(), f, indent=2)
        print(f"  ✓ Saved: {schema_file}")
        
        print("\n" + "="*60)
        print("✓ TRANSLATION COMPLETE!")
        print("="*60)
        print(f"\nOutput directory: {output_dir}")
        print(f"Solidity contract: {len(solidity.splitlines())} lines")
        print(f"ABI elements: {len(abi)}")
        
        return {
            'schema': schema,
            'solidity': solidity,
            'abi': abi
        }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python run_translation.py <path_to_contract.pdf>")
        print("Example: python run_translation.py 'contracts/Simple Rental Agreement v1.pdf'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    
    try:
        translator = SimpleContractTranslator()
        result = translator.translate_contract(input_file, output_dir)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)