// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

/// @title RentalAgreement
/// @notice A generic rental agreement between a landlord and a tenant
contract RentalAgreement {
    address public landlord;
    address public tenant;
    uint256 public monthlyRent;
    uint256 public securityDeposit;
    uint256 public leaseStart;
    string public propertyAddress;
    bool public depositPaid;
    mapping(uint256 => bool) public rentPaid; // month => paid
    mapping(uint256 => bool) public rentConfirmed; // month => confirmed

    event DepositPaid(address indexed tenant, uint256 amount);
    event RentPaid(address indexed tenant, uint256 month, uint256 amount);
    event RentConfirmed(address indexed landlord, uint256 month);
    event LandlordTransferred(address indexed previousLandlord, address indexed newLandlord);

    modifier onlyTenant() {
        require(msg.sender == tenant, "Only tenant can call this");
        _;
    }

    modifier onlyLandlord() {
        require(msg.sender == landlord, "Only landlord can call this");
        _;
    }

    constructor(
        address _landlord,
        address _tenant,
        uint256 _monthlyRent,
        uint256 _securityDeposit,
        uint256 _leaseStart,
        string memory _propertyAddress
    ) {
        landlord = _landlord;
        tenant = _tenant;
        monthlyRent = _monthlyRent;
        securityDeposit = _securityDeposit;
        leaseStart = _leaseStart;
        propertyAddress = _propertyAddress;
        depositPaid = false;
    }

    /// @notice Tenant pays the security deposit
    function payDeposit() external payable onlyTenant {
        require(!depositPaid, "Deposit already paid");
        require(msg.value == securityDeposit, "Incorrect deposit amount");
        depositPaid = true;
        payable(landlord).transfer(msg.value);
        emit DepositPaid(msg.sender, msg.value);
    }

    /// @notice Tenant pays rent for a given month (month = 1 for first month, etc.)
    function payRent(uint256 month) external payable onlyTenant {
        require(depositPaid, "Deposit not paid");
        require(msg.value == monthlyRent, "Incorrect rent amount");
        require(!rentPaid[month], "Rent already paid for this month");
        rentPaid[month] = true;
        payable(landlord).transfer(msg.value);
        emit RentPaid(msg.sender, month, msg.value);
    }

    /// @notice Landlord confirms rent payment for a given month
    function confirmRent(uint256 month) external onlyLandlord {
        require(rentPaid[month], "Rent not paid for this month");
        require(!rentConfirmed[month], "Rent already confirmed for this month");
        rentConfirmed[month] = true;
        emit RentConfirmed(msg.sender, month);
    }

    /// @notice Landlord can transfer ownership to a new landlord address
    function transferAddress(address newLandlord) external onlyLandlord {
        require(newLandlord != address(0), "Invalid address");
        address previousLandlord = landlord;
        landlord = newLandlord;
        emit LandlordTransferred(previousLandlord, newLandlord);
    }
}