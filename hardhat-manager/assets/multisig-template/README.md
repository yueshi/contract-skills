# Multisig Wallet Template

A production-ready multisig wallet template with Gnosis Safe compatibility.

## Features

- **Basic Multisig** - Simple multisig wallet (Tier 1)
- **Timelock Multisig** - Advanced multisig with delay (Tier 2)
- **Gnosis Safe Compatible** - Import into Gnosis Safe UI
- **Multi-tier Confirmations** - Based on transaction value
- **Emergency Mode** - Fast execution for urgent transactions
- **Full Test Coverage** - 90+ comprehensive tests

## Quick Start

### 1. Create Project

```bash
# From the hardhat-manager directory
python3 scripts/setup_multisig.py \
    --type basic \
    --config basic \
    --name my-multisig
```

### 2. Configure

Edit `config/multisig.config.js`:
```javascript
basic: {
  owners: [
    "0x...", // Owner 1
    "0x...", // Owner 2
    "0x..."  // Owner 3
  ],
  requiredConfirmations: 2
}
```

### 3. Install & Deploy

```bash
cd my-multisig
npm install
npm run deploy:local
```

## Documentation

For complete documentation, see:
- **Complete Guide**: `/MULTISIG_TEMPLATE_GUIDE.md`
- **Implementation Summary**: `/MULTISIG_IMPLEMENTATION_SUMMARY.md`

## Templates

### Basic Multisig
- Simple multisig wallet
- ETH and ERC20 support
- Gnosis Safe compatible
- **Use case**: Small teams, simple fund management

### Timelock Multisig
- All basic features
- Transaction timelock (24h - 30 days)
- Multi-tier confirmations
- Emergency transactions
- **Use case**: DAOs, project funds, DeFi governance

## Deployment

| Network | Command |
|---------|---------|
| Local | `npm run deploy:local` |
| Goerli | `npm run deploy:goerli` |
| Sepolia | `npm run deploy:sepolia` |
| Mainnet | `npm run deploy:mainnet` |
| Polygon | `npm run deploy:polygon` |

## Testing

```bash
npm test                 # All tests
npm run test:multisig    # Basic multisig tests
npm run test:timelock    # Timelock tests
npm run coverage         # Coverage report
```

## Security

- ✅ OpenZeppelin standards
- ✅ Reentrancy protection
- ✅ Access control
- ✅ Pausable mechanism
- ✅ Timelock security
- ✅ Comprehensive testing

## License

MIT
