# Basic Hardhat Project

This is a basic Hardhat project template that provides a solid foundation for smart contract development.

## Project Structure

```
.
├── contracts/           # Smart contract source files
├── scripts/             # Deployment and utility scripts
├── test/               # Test files
├── hardhat.config.js   # Hardhat configuration
├── package.json        # Node.js dependencies
└── README.md          # This file
```

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Setup

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your private keys and API keys:

```
PRIVATE_KEY=your_private_key_here
INFURA_API_KEY=your_infura_api_key_here
ETHERSCAN_API_KEY=your_etherscan_api_key_here
```

### 3. Compile Contracts

```bash
npx hardhat compile
```

### 4. Run Tests

```bash
npx hardhat test
```

### 5. Deploy Contracts

To deploy on the local Hardhat network:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

To deploy on a testnet:

```bash
npx hardhat run scripts/deploy.js --network goerli
```

## Available Scripts

- `npx hardhat compile` - Compile your smart contracts
- `npx hardhat test` - Run your test suite
- `npx hardhat node` - Start a local Hardhat network
- `npx hardhat run <script>` - Run a specific script
- `npx hardhat console` - Open an interactive console

## Testing

Run all tests:

```bash
npx hardhat test
```

Run a specific test file:

```bash
npx hardhat test test/MyContract.test.js
```

Run tests with gas reporting:

```bash
REPORT_GAS=true npx hardhat test
```

## Deployment

### Local Deployment

1. Start a local Hardhat node:
   ```bash
   npx hardhat node
   ```

2. In a separate terminal, deploy:
   ```bash
   npx hardhat run scripts/deploy.js --network localhost
   ```

### Testnet Deployment

1. Configure your `.env` file with the testnet settings
2. Deploy:
   ```bash
   npx hardhat run scripts/deploy.js --network goerli
   ```

### Mainnet Deployment

⚠️ **Warning**: Always test thoroughly on testnets before deploying to mainnet.

```bash
npx hardhat run scripts/deploy.js --network mainnet
```

## Contract Verification

After deployment, verify your contracts on Etherscan:

```bash
npx hardhat verify --network <network> <contract-address> "<constructor-args>"
```

## Gas Optimization

Use the gas reporter to analyze gas usage:

```bash
REPORT_GAS=true npx hardhat test
```

## Security

Before deploying to production:

1. ✅ Run all tests and ensure 100% pass rate
2. ✅ Check test coverage: `npx hardhat coverage`
3. ✅ Run static analysis: `slither contracts/`
4. ✅ Review security checklist in the documentation
5. ✅ Consider a professional security audit for mainnet deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Resources

- [Hardhat Documentation](https://hardhat.org/docs)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/4.x/)
- [Solidity by Example](https://solidity-by-example.org/)
- [Ethereum Smart Contract Security](https://consensys.github.io/smart-contract-best-practices/)

## Support

This project was created using the Hardhat Manager skill. For additional support and advanced features, refer to the skill documentation.