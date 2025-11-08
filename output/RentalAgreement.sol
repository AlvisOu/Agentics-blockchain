// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title RentalAgreement
 * @dev Smart contract for rental agreement
 * Property: 123 Main St
 */
contract RentalAgreement {
    
    // State variables
    address public landlord;
    address public tenant;
    uint256 public monthlyRent;
    uint256 public securityDeposit;
    uint256 public leaseStart;
    string public propertyAddress;
    bool public depositPaid;
    
    // Track rent payments by month (timestamp)
    mapping(uint256 => bool) public rentPaid;
    mapping(uint256 => bool) public rentConfirmed;
    
    // Events
    event RentPaid(address indexed tenant, uint256 month, uint256 amount);
    event DepositPaid(address indexed tenant, uint256 amount);
    event RentConfirmed(address indexed landlord, uint256 month);
    event LandlordTransferred(address indexed previousLandlord, address indexed newLandlord);
    
    // Modifiers
    modifier onlyLandlord() {
        require(msg.sender == landlord, "Only landlord can call this");
        _;
    }
    
    modifier onlyTenant() {
        require(msg.sender == tenant, "Only tenant can call this");
        _;
    }
    
    /**
     * @dev Constructor to initialize the rental agreement
     */
    constructor(
        address _landlord,
        address _tenant,
        uint256 _monthlyRent,
        uint256 _securityDeposit,
        uint256 _leaseStart,
        string memory _propertyAddress
    ) {
        require(_landlord != address(0), "Invalid landlord address");
        require(_tenant != address(0), "Invalid tenant address");
        require(_monthlyRent > 0, "Rent must be greater than 0");
        
        landlord = _landlord;
        tenant = _tenant;
        monthlyRent = _monthlyRent;
        securityDeposit = _securityDeposit;
        leaseStart = _leaseStart;
        propertyAddress = _propertyAddress;
        depositPaid = false;
    }
    
    /**
     * @dev Tenant pays security deposit
     */
    function payDeposit() external payable onlyTenant {
        require(!depositPaid, "Deposit already paid");
        require(msg.value == securityDeposit, "Incorrect deposit amount");
        
        depositPaid = true;
        emit DepositPaid(msg.sender, msg.value);
    }
    
    /**
     * @dev Tenant pays monthly rent
     * @param month The month being paid (timestamp)
     */
    function payRent(uint256 month) external payable onlyTenant {
        require(depositPaid, "Deposit must be paid first");
        require(msg.value == monthlyRent, "Incorrect rent amount");
        require(!rentPaid[month], "Rent already paid for this month");
        require(month >= leaseStart, "Cannot pay rent before lease start");
        
        rentPaid[month] = true;
        emit RentPaid(msg.sender, month, msg.value);
    }
    
    /**
     * @dev Landlord confirms receipt of rent payment
     * @param month The month to confirm
     */
    function confirmRent(uint256 month) external onlyLandlord {
        require(rentPaid[month], "Rent not paid for this month");
        require(!rentConfirmed[month], "Rent already confirmed");
        
        rentConfirmed[month] = true;
        
        // Transfer rent to landlord
        payable(landlord).transfer(monthlyRent);
        
        emit RentConfirmed(msg.sender, month);
    }
    
    /**
     * @dev Transfer landlord rights (e.g., property sale)
     * @param newLandlord Address of new landlord
     */
    function transferAddress(address newLandlord) external onlyLandlord {
        require(newLandlord != address(0), "Invalid new landlord address");
        
        address previousLandlord = landlord;
        landlord = newLandlord;
        
        emit LandlordTransferred(previousLandlord, newLandlord);
    }
    
    /**
     * @dev Get contract balance
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}