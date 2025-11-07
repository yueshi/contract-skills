#!/usr/bin/env python3
"""
Smart Contract Code Generator - Simple Version

Automatically generates smart contracts, tests, and deployment scripts
based on user requirements and templates.

Usage:
    python3 contract_generator.py --type <contract-type> --name <contract-name>
    python3 contract_generator.py --interactive
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime


class ContractGenerator:
    def __init__(self):
        self.output_dir = Path("contracts")
        self.test_dir = Path("test")
        self.scripts_dir = Path("scripts")

        # Ensure directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.test_dir.mkdir(exist_ok=True)
        self.scripts_dir.mkdir(exist_ok=True)

    def generate_erc20_token(self, name, symbol, decimals=18, initial_supply=None):
        """Generate ERC20 token contract."""

        if initial_supply is None:
            initial_supply = 1000000

        # Create ERC20 contract code using string concatenation
        contract_parts = [
            "// SPDX-License-Identifier: MIT",
            "pragma solidity ^0.8.19;",
            "",
            'import "@openzeppelin/contracts/token/ERC20/ERC20.sol";',
            'import "@openzeppelin/contracts/access/Ownable.sol";',
            "",
            "/**",
            f" * @title {name}",
            " * @dev ERC20 token with basic features",
            " */",
            f"contract {name.replace(' ', '')} is ERC20, Ownable {{",
            "",
            f'    constructor() ERC20("{name}", "{symbol}") {{',
            f"        _mint(msg.sender, {initial_supply} * 10**{decimals});",
            "    }",
            "",
            "    function mint(address to, uint256 amount) external onlyOwner {",
            "        _mint(to, amount);",
            "    }",
            "",
            "    function burn(uint256 amount) external {",
            "        _burn(msg.sender, amount);",
            "    }",
            "}"
        ]

        return "\n".join(contract_parts)

    def generate_erc721_nft(self, name, symbol, max_supply=None):
        """Generate ERC721 NFT contract."""

        if max_supply is None:
            max_supply = 10000

        contract_parts = [
            "// SPDX-License-Identifier: MIT",
            "pragma solidity ^0.8.19;",
            "",
            'import "@openzeppelin/contracts/token/ERC721/ERC721.sol";',
            'import "@openzeppelin/contracts/access/Ownable.sol";',
            'import "@openzeppelin/contracts/utils/Counters.sol";',
            "",
            "/**",
            f" * @title {name}",
            " * @dev ERC721 NFT with basic features",
            " */",
            f"contract {name.replace(' ', '')} is ERC721, Ownable {{",
            "    using Counters for Counters.Counter;",
            "    Counters.Counter private _tokenIdCounter;",
            f"    uint256 public maxSupply = {max_supply};",
            "",
            f'    constructor() ERC721("{name}", "{symbol}") {{',
            "        // Initialize",
            "    }",
            "",
            "    function safeMint(address to) public onlyOwner {",
            "        require(_tokenIdCounter.current() < maxSupply, \"Max supply reached\");",
            "        _tokenIdCounter.increment();",
            "        uint256 tokenId = _tokenIdCounter.current();",
            "        _safeMint(to, tokenId);",
            "    }",
            "",
            "    function totalSupply() public view returns (uint256) {",
            "        return _tokenIdCounter.current();",
            "    }",
            "}"
        ]

        return "\n".join(contract_parts)

    def generate_test_file(self, contract_name, contract_type):
        """Generate test file for the contract."""

        if contract_type == "erc20":
            test_content = f"""const {{ expect }} = require("chai");
const {{ ethers }} = require("hardhat");

describe("{contract_name}", function () {{
  let token;
  let owner, user1, user2;

  beforeEach(async function () {{
    [owner, user1, user2] = await ethers.getSigners();

    const ContractFactory = await ethers.getContractFactory("{contract_name}");
    token = await ContractFactory.deploy();
    await token.deployed();
  }});

  describe("Deployment", function () {{
    it("Should set the right owner", async function () {{
      expect(await token.owner()).to.equal(owner.address);
    }});

    it("Should have correct name and symbol", async function () {{
      expect(await token.name()).to.equal("{contract_name}");
    }});

    it("Should have initial supply", async function () {{
      const totalSupply = await token.totalSupply();
      expect(totalSupply).to.equal(await token.balanceOf(owner.address));
    }});
  }});

  describe("Minting", function () {{
    it("Should allow owner to mint", async function () {{
      const amount = ethers.utils.parseEther("1000");
      await expect(token.connect(owner).mint(user1.address, amount))
        .to.emit(token, "Transfer");
    }});
  }});
}}"""
        else:
            test_content = f"""const {{ expect }} = require("chai");
const {{ ethers }} = require("hardhat");

describe("{contract_name}", function () {{
  let contract;
  let owner, user1;

  beforeEach(async function () {{
    [owner, user1] = await ethers.getSigners();

    const ContractFactory = await ethers.getContractFactory("{contract_name}");
    contract = await ContractFactory.deploy();
    await contract.deployed();
  }});

  describe("Deployment", function () {{
    it("Should deploy successfully", async function () {{
      expect(contract.address).to.be.a("string");
    }});
  }});
}}"""

        return test_content

    def generate_deployment_script(self, contract_name, constructor_args=None):
        """Generate deployment script for the contract."""

        if constructor_args:
            args_str = ", ".join([f'"{arg}"' if isinstance(arg, str) else str(arg) for arg in constructor_args])
            args_with_commas = f"({args_str})"
        else:
            args_with_commas = ""

        script_content = f"""const {{ ethers }} = require("hardhat");

async function main() {{
  console.log("Deploying {contract_name}...");

  const ContractFactory = await ethers.getContractFactory("{contract_name}");
  const contract = await ContractFactory.deploy{args_with_commas};

  await contract.deployed();

  console.log("✅ {contract_name} deployed to:", contract.address);
}}

main()
  .then(() => process.exit(0))
  .catch((error) => {{
    console.error(error);
    process.exit(1);
  }});"""

        return script_content

    def save_contract(self, contract_name, contract_code):
        """Save contract code to file."""
        contract_file = self.output_dir / f"{contract_name}.sol"
        with open(contract_file, 'w') as f:
            f.write(contract_code)

        print(f"✅ Contract saved to: {contract_file}")
        return contract_file

    def save_test(self, contract_name, test_code):
        """Save test code to file."""
        test_file = self.test_dir / f"{contract_name}.test.js"
        with open(test_file, 'w') as f:
            f.write(test_code)

        print(f"✅ Test saved to: {test_file}")
        return test_file

    def save_deployment_script(self, contract_name, script_code):
        """Save deployment script to file."""
        script_file = self.scripts_dir / f"deploy_{contract_name.lower()}.js"
        with open(script_file, 'w') as f:
            f.write(script_code)

        print(f"✅ Deployment script saved to: {script_file}")
        return script_file

    def generate_contract(self, contract_type, name, **kwargs):
        """Main contract generation function."""
        print(f"🚀 Generating {contract_type.upper()} contract: {name}")

        contract_code = None
        constructor_args = []

        if contract_type == "erc20":
            symbol = kwargs.get("symbol", name[:3].upper())
            decimals = kwargs.get("decimals", 18)
            initial_supply = kwargs.get("initial_supply", 1000000)

            contract_code = self.generate_erc20_token(name, symbol, decimals, initial_supply)
            constructor_args = [name, symbol]

        elif contract_type == "nft":
            symbol = kwargs.get("symbol", "NFT")
            max_supply = kwargs.get("max_supply", 10000)

            contract_code = self.generate_erc721_nft(name, symbol, max_supply)
            constructor_args = [name, symbol]

        else:
            raise ValueError(f"Unsupported contract type: {contract_type}")

        # Save files
        contract_file = self.save_contract(name.replace(' ', ''), contract_code)
        test_file = self.save_test(name.replace(' ', ''), self.generate_test_file(name.replace(' ', ''), contract_type))
        script_file = self.save_deployment_script(name.replace(' ', ''), self.generate_deployment_script(name.replace(' ', ''), constructor_args))

        print(f"\n🎉 Contract generation completed!")
        print(f"📁 Files created:")
        print(f"   Contract: {contract_file}")
        print(f"   Test: {test_file}")
        print(f"   Deployment: {script_file}")
        print(f"\n📝 Next steps:")
        print(f"1. Review the generated contract code")
        print(f"2. Run tests: npx hardhat test")
        print(f"3. Compile: npx hardhat compile")
        print(f"4. Deploy: npx hardhat run scripts/deploy_{name.replace(' ', '').lower()}.js --network <network>")

        return {
            contract: contract_file,
            test: test_file,
            deployment: script_file
        }

    def interactive_mode(self):
        """Interactive contract generation mode."""
        print("🎯 Interactive Contract Generator")
        print("=" * 50)

        # Get contract type
        print("\nAvailable contract types:")
        print("1. ERC20 Token")
        print("2. ERC721 NFT")

        while True:
            try:
                choice = input("\nSelect contract type (1-2): ").strip()
                if choice in ["1", "2"]:
                    break
                print("Invalid choice. Please select 1 or 2.")
            except KeyboardInterrupt:
                print("\n❌ Generation cancelled")
                return

        contract_types = {"1": "erc20", "2": "nft"}
        contract_type = contract_types[choice]

        # Get contract name
        while True:
            try:
                name = input("\nEnter contract name: ").strip()
                if name and name.replace(' ', '').isalnum():
                    break
                print("Invalid name. Use letters and numbers only.")
            except KeyboardInterrupt:
                print("\n❌ Generation cancelled")
                return

        # Get additional parameters based on type
        kwargs = {}

        if contract_type == "erc20":
            symbol = input("Enter token symbol (default: " + name[:3].upper() + "): ").strip()
            if symbol:
                kwargs["symbol"] = symbol

            decimals = input("Enter decimals (default: 18): ").strip()
            if decimals and decimals.isdigit():
                kwargs["decimals"] = int(decimals)

            supply = input("Enter initial supply (default: 1000000): ").strip()
            if supply and supply.isdigit():
                kwargs["initial_supply"] = int(supply)

        elif contract_type == "nft":
            symbol = input("Enter NFT symbol (default: NFT): ").strip()
            if symbol:
                kwargs["symbol"] = symbol

            max_supply = input("Enter max supply (default: 10000): ").strip()
            if max_supply and max_supply.isdigit():
                kwargs["max_supply"] = int(max_supply)

        # Generate contract
        try:
            self.generate_contract(contract_type, name, **kwargs)
        except Exception as e:
            print(f"❌ Generation failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate smart contracts")
    parser.add_argument("--type", choices=["erc20", "nft"],
                       help="Contract type to generate")
    parser.add_argument("--name", help="Contract name")
    parser.add_argument("--symbol", help="Token/NFT symbol")
    parser.add_argument("--decimals", type=int, help="Token decimals")
    parser.add_argument("--initial-supply", type=int, help="Initial token supply")
    parser.add_argument("--max-supply", type=int, help="Maximum NFT supply")
    parser.add_argument("--interactive", action="store_true",
                       help="Interactive mode")

    args = parser.parse_args()

    generator = ContractGenerator()

    if args.interactive:
        generator.interactive_mode()
    elif args.type and args.name:
        kwargs = {}
        if args.symbol: kwargs["symbol"] = args.symbol
        if args.decimals: kwargs["decimals"] = args.decimals
        if args.initial_supply: kwargs["initial_supply"] = args.initial_supply
        if args.max_supply: kwargs["max_supply"] = args.max_supply

        generator.generate_contract(args.type, args.name, **kwargs)
    else:
        print("❌ Please provide either --interactive mode or --type and --name")
        parser.print_help()


if __name__ == "__main__":
    main()