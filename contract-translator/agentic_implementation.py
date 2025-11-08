import json
from pathlib import Path
from typing import Dict, List, Optional
import PyPDF2
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

from agentics import LLM, Program, user_message, system_message

load_dotenv()

# ==================== PYDANTIC SCHEMAS ====================

class PartyRole(str, Enum):
    """Common party roles across all contracts"""
    BUYER = "buyer"
    SELLER = "seller"
    LANDLORD = "landlord"
    TENANT = "tenant"
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    LENDER = "lender"
    BORROWER = "borrower"
    SERVICE_PROVIDER = "service_provider"
    CLIENT = "client"
    INVESTOR = "investor"
    COMPANY = "company"
    OTHER = "other"

class ContractType(str, Enum):
    """All supported contract types"""
    RENTAL = "rental_agreement"
    EMPLOYMENT = "employment_contract"
    SALES = "sales_agreement"
    SERVICE = "service_agreement"
    LOAN = "loan_agreement"
    NDA = "non_disclosure_agreement"
    PARTNERSHIP = "partnership_agreement"
    INVESTMENT = "investment_agreement"
    LEASE = "lease_agreement"
    PURCHASE = "purchase_agreement"
    OTHER = "other"

class ContractParty(BaseModel):
    name: str
    role: str  
    address: Optional[str] = None 
    email: Optional[str] = None
    entity_type: Optional[str] = None

class FinancialTerm(BaseModel):
    """Universal financial term"""
    amount: float
    currency: str = "ETH"
    purpose: str 
    frequency: Optional[str] = None 
    due_date: Optional[str] = None

class ContractDate(BaseModel):
    date_type: str 
    value: Optional[str] = None
    day_of_month: Optional[int] = None
    frequency: Optional[str] = None

class ContractObligation(BaseModel):
    party: str  # Who has this obligation
    description: str
    deadline: Optional[str] = None
    penalty_for_breach: Optional[str] = None

class ContractAsset(BaseModel):
    type: str
    description: str
    location: Optional[str] = None
    quantity: Optional[int] = None
    value: Optional[float] = None

class UniversalContractSchema(BaseModel):
    contract_type: str
    title: Optional[str] = None
    parties: List[ContractParty]
    financial_terms: List[FinancialTerm] = []
    dates: List[ContractDate] = []
    assets: List[ContractAsset] = []
    obligations: List[ContractObligation] = []
    special_terms: List[str] = []
    conditions: Dict[str, Any] = {}
    termination_conditions: List[str] = []

class UniversalContractParserProgram(Program):
    def forward(self, contract_text: str, lm: LLM) -> UniversalContractSchema:
        """Parse any contract type"""
        
        messages = [
            system_message(
                """You are an expert contract analyst who can parse ANY type of legal agreement.
                
                You handle:
                - Rental agreements
                - Employment contracts
                - Sales agreements
                - Service contracts
                - Loan agreements
                - NDAs
                - Partnership agreements
                - Investment agreements
                - And more...
                
                Your job: Extract ALL relevant information regardless of contract type."""
            ),
            user_message(
                f"""Analyze this contract and extract ALL structured information.

CONTRACT TEXT:
{contract_text}

First, determine the contract type, then extract all relevant data.

Return ONLY valid JSON with this structure:
{{
    "contract_type": "rental|employment|sales|service|loan|nda|partnership|investment|other",
    "title": "optional contract title",
    "parties": [
        {{
            "name": "party name",
            "role": "their role (buyer/seller/landlord/tenant/employer/etc)",
            "address": "optional blockchain address",
            "email": "optional",
            "entity_type": "individual|company|organization"
        }}
    ],
    "financial_terms": [
        {{
            "amount": number,
            "currency": "ETH|USD|etc",
            "purpose": "payment|deposit|salary|price|etc",
            "frequency": "one-time|monthly|annual|etc",
            "due_date": "optional"
        }}
    ],
    "dates": [
        {{
            "date_type": "start|end|delivery|payment_due|etc",
            "value": "date string",
            "day_of_month": number or null,
            "frequency": "optional"
        }}
    ],
    "assets": [
        {{
            "type": "real_estate|goods|services|intellectual_property|etc",
            "description": "what is it",
            "location": "optional",
            "quantity": number or null,
            "value": number or null
        }}
    ],
    "obligations": [
        {{
            "party": "who",
            "description": "what they must do",
            "deadline": "optional",
            "penalty_for_breach": "optional"
        }}
    ],
    "special_terms": ["list of special conditions"],
    "conditions": {{}},
    "termination_conditions": ["how contract can be terminated"]
}}

Extract EVERYTHING relevant to this specific contract type."""
            )
        ]
        
        response = lm.chat(messages=messages)
        response_text = str(response).strip()

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        
        parsed = json.loads(response_text)
        return UniversalContractSchema(**parsed)


class UniversalSolidityGeneratorProgram(Program):
    """Generates Solidity for ANY contract type"""
    
    def forward(self, schema: UniversalContractSchema, lm: LLM) -> str:
        """Generate contract-type-specific Solidity"""
 
        requirements = self._get_requirements_for_type(schema.contract_type)
        
        messages = [
            system_message(
                f"""You are a Solidity expert who generates smart contracts for {schema.contract_type}.
                
                You understand the specific requirements and patterns for this contract type.
                You write secure, production-ready code following best practices."""
            ),
            user_message(
                f"""Generate a Solidity ^0.8.0 smart contract for this {schema.contract_type}:

{schema.json(indent=2)}

Requirements for {schema.contract_type}:
{requirements}

Generate a complete, secure smart contract that:
1. Handles all parties: {[p.name + ' (' + p.role + ')' for p in schema.parties]}
2. Manages financial terms: {[f"{t.amount} {t.currency} for {t.purpose}" for t in schema.financial_terms]}
3. Tracks obligations and conditions
4. Includes appropriate events
5. Has proper access control
6. Follows security best practices

Return ONLY the Solidity code."""
            )
        ]
        
        response = lm.chat(messages=messages)
        # ... parse and return
    
    def _get_requirements_for_type(self, contract_type: str) -> str:
        """Get contract-type-specific requirements"""
        
        requirements_map = {
            'rental_agreement': """
                - Monthly rent payment function
                - Security deposit handling
                - Lease term tracking
                - Property address storage
            """,
            'employment_contract': """
                - Salary payment function
                - Employment term tracking
                - Position/role storage
                - Termination conditions
            """,
            'sales_agreement': """
                - Purchase price payment
                - Delivery confirmation
                - Goods/asset transfer
                - Warranty tracking
            """,
            'service_agreement': """
                - Milestone payment system
                - Service delivery confirmation
                - Scope of work tracking
                - Performance metrics
            """,
            'loan_agreement': """
                - Principal amount tracking
                - Interest calculation
                - Repayment schedule
                - Collateral management
            """,
            # Add more types...
        }
        
        return requirements_map.get(contract_type, """
            - Generic payment handling
            - Term tracking
            - Obligation management
            - Event logging
        """)


class SecurityAuditorProgram(Program):
    """IBM Agentics Program for security auditing"""
    
    def forward(self, solidity_code: str, lm: LLM) -> Dict:
        """Perform security audit"""
        
        messages = [
            system_message(
                "You are a blockchain security expert. "
                "Audit smart contracts for vulnerabilities and provide detailed reports."
            ),
            user_message(
                f"""Audit this contract for security issues:

{solidity_code}

Return ONLY valid JSON:
{{
    "severity_level": "none|low|medium|high",
    "approved": boolean,
    "issues": ["list of issues"],
    "recommendations": ["improvements"],
    "vulnerability_count": number,
    "security_score": "A|B|C|D|F"
}}"""
            )
        ]
        
        response = lm.chat(messages=messages)
        audit_text = str(response).strip()
        
        if "```json" in audit_text:
            audit_text = audit_text.split("```json")[1].split("```")[0].strip()
        elif "```" in audit_text:
            audit_text = audit_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(audit_text)


class ABIGeneratorProgram(Program):
    
    def forward(self, solidity_code: str, lm: LLM) -> List[Dict]:
        """Generate ABI"""
        
        messages = [
            system_message(
                "You are an Ethereum ABI expert. "
                "Generate accurate ABI specifications from Solidity contracts."
            ),
            user_message(
                f"""Generate complete ABI for:

{solidity_code}

Include constructor, all functions, and events with correct types.
Return ONLY the JSON array."""
            )
        ]
        
        response = lm.chat(messages=messages)
        abi_text = str(response).strip()
        
        if "```json" in abi_text:
            abi_text = abi_text.split("```json")[1].split("```")[0].strip()
        elif "```" in abi_text:
            abi_text = abi_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(abi_text)

class IBMAgenticContractTranslator:
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize translator
        
        Args:
            model: LLM model to use (default: gpt-4o-mini for OpenAI)
        
        Note: IBM Agentics requires OPENAI_API_KEY in environment
        """

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY required in .env file. "
                "IBM Agentics uses OpenAI models by default."
            )
        
        self.llm = LLM(model=model)
        print(f"✓ IBM Agentics LLM initialized with {model}")
        print("🤖 Initializing IBM Agentics Programs...")
        self.parser = UniversalContractParserProgram()
        self.generator = UniversalSolidityGeneratorProgram()
        self.auditor = SecurityAuditorProgram()
        self.abi_generator = ABIGeneratorProgram()
        print("✓ All Programs initialized\n")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        print(f"📄 Reading PDF: {pdf_path}")
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    
    def translate_contract(
        self, 
        input_path: str, 
        output_dir: str = "./output",
        require_audit_approval: bool = True
    ) -> Dict:
        """
        Complete translation workflow using IBM Agentics Programs
        """
        
        print("\n" + "="*70)
        print("IBM AGENTICS CONTRACT TRANSLATOR")
        print("="*70)
        
        results = {}
        
        print("\n[Phase 1/5] Document Processing")
        if input_path.endswith('.pdf'):
            contract_text = self.extract_text_from_pdf(input_path)
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                contract_text = f.read()
        print(f"✓ Extracted {len(contract_text)} characters")
        
        print("\n[Phase 2/5] Contract Analysis (Parser Program)")
        schema = self.parser.forward(contract_text, self.llm)
        results['schema'] = schema
        print(f"✓ Parsed: {len(schema.parties)} parties, {len(schema.monetary_amounts)} amounts")
        
        print("\n[Phase 3/5] Code Generation (Generator Program)")
        solidity_code = self.generator.forward(schema, self.llm)
        results['solidity'] = solidity_code
        print(f"✓ Generated {len(solidity_code.splitlines())} lines")
        
        print("\n[Phase 4/5] Security Analysis (Auditor Program)")
        audit_report = self.auditor.forward(solidity_code, self.llm)
        results['audit'] = audit_report
        severity = audit_report.get('severity_level', 'unknown')
        score = audit_report.get('security_score', 'N/A')
        print(f"✓ Audit: Severity={severity}, Score={score}")
        
        if require_audit_approval and not audit_report.get('approved', False):
            print("\n⚠️  Security issues detected!")
            for i, issue in enumerate(audit_report.get('issues', [])[:3], 1):
                print(f"   {i}. {issue}")
            
            response = input("\n   Continue? (yes/no): ").lower()
            if response != 'yes':
                raise Exception("Halted due to security concerns")
        
        print("\n[Phase 5/5] Interface Generation (ABI Program)")
        abi = self.abi_generator.forward(solidity_code, self.llm)
        results['abi'] = abi
        print(f"✓ Generated {len(abi)} ABI elements")
        
        self._save_outputs(results, output_dir)
        
        print("\n" + "="*70)
        print("✅ TRANSLATION COMPLETE")
        print("="*70)
        
        return results
    
    def _save_outputs(self, results: Dict, output_dir: str):
        """Save all outputs"""
        
        print("\n💾 Saving outputs...")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        with open(output_path / "RentalAgreement.sol", 'w') as f:
            f.write(results['solidity'])
        print(f"   ✓ RentalAgreement.sol")

        with open(output_path / "RentalAgreement.abi.json", 'w') as f:
            json.dump(results['abi'], f, indent=2)
        print(f"   ✓ RentalAgreement.abi.json")

        with open(output_path / "contract_schema.json", 'w') as f:
            json.dump(results['schema'].dict(), f, indent=2)
        print(f"   ✓ contract_schema.json")
 
        with open(output_path / "security_audit.json", 'w') as f:
            json.dump(results['audit'], f, indent=2)
        print(f"   ✓ security_audit.json")
 
        schema = results['schema']
        audit = results['audit']
        
        readme = f"""# IBM Agentics Contract Translation

## Contract Summary
- **Parties**: {', '.join(p.name for p in schema.parties)}
- **Property**: {schema.property_details.address}
- **Terms**: {len(schema.monetary_amounts)} financial terms

## Security Audit
- **Status**: {'✅ APPROVED' if audit.get('approved') else '⚠️ REVIEW NEEDED'}
- **Severity**: {audit['severity_level'].upper()}
- **Score**: {audit.get('security_score', 'N/A')}

## Generated Files
1. RentalAgreement.sol ({len(results['solidity'].splitlines())} lines)
2. RentalAgreement.abi.json ({len(results['abi'])} elements)
3. contract_schema.json
4. security_audit.json
"""     
        with open(output_path / "README.md", 'w') as f:
            f.write(readme)
        print(f"   ✓ README.md")

def main():
    """CLI entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python agentic_implementation_final.py <contract.pdf> [output_dir]")
        print("\nRequirements:")
        print("  - OPENAI_API_KEY in .env")
        print("  - PDF contract file")
        print("\nExample:")
        print("  python agentic_implementation_final.py 'contracts/rental.pdf'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    
    try:
        translator = IBMAgenticContractTranslator()
        results = translator.translate_contract(input_file, output_dir)
        
        print("\n📊 Summary:")
        print(f"   Parties: {len(results['schema'].parties)}")
        print(f"   Solidity: {len(results['solidity'].splitlines())} lines")
        print(f"   Security: {results['audit']['severity_level']}")
        print(f"   ABI: {len(results['abi'])} elements")
        print(f"\n📁 Output: {output_dir}/")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()