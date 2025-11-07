/**
 * Multisig Wallet Configuration
 *
 * This file contains configuration templates for different multisig scenarios.
 * Copy and modify based on your needs.
 */

module.exports = {
  // Basic multisig configuration (tier 1)
  basic: {
    name: "Basic Multisig Wallet",
    description: "Simple multisig wallet for small teams",
    owners: [
      // Add owner addresses here
      // "0x...",
      // "0x...",
      // "0x..."
    ],
    requiredConfirmations: 2,
    safeModeEnabled: true,
    gnosisCompatibility: true,
    useCase: "team_funds"
  },

  // DAO multisig configuration (tier 2)
  dao: {
    name: "DAO Treasury Multisig",
    description: "Treasury management for DAO with tiered approvals",
    owners: [
      // DAO core team
      // "0x...",
      // "0x...",
      // Community representatives
      // "0x...",
      // "0x..."
    ],
    requiredConfirmations: 3,
    safeModeEnabled: true,
    gnosisCompatibility: true,
    timelockEnabled: true,
    useCase: "dao_treasury",

    // Timelock settings
    timelock: {
      // Minimum delay for transactions
      minimumDelay: 24 * 60 * 60, // 24 hours in seconds
      // Maximum delay for transactions
      maximumDelay: 30 * 24 * 60 * 60, // 30 days in seconds
      // Grace period after eta
      gracePeriod: 7 * 24 * 60 * 60, // 7 days in seconds

      // Tier thresholds (in wei)
      tier1Threshold: "10", // 10 ETH
      tier2Threshold: "100", // 100 ETH

      // Confirmation requirements per tier
      tier1Confirmations: 2,
      tier2Confirmations: 3,
      tier3Confirmations: 4,

      // Emergency transaction settings
      emergencyDelay: 2 * 60 * 60, // 2 hours in seconds
      emergencyGracePeriod: 24 * 60 * 60 // 24 hours in seconds
    },

    // Timelock administrators (can queue/execute transactions)
    timelockAdmins: [
      // "0x...",
      // "0x..."
    ],

    // Spending limits (optional)
    spendingLimits: {
      enabled: true,
      dailyLimit: "50", // 50 ETH per day
      weeklyLimit: "200", // 200 ETH per week
      monthlyLimit: "1000" // 1000 ETH per month
    }
  },

  // Project fund management (tier 2)
  project: {
    name: "Project Fund Multisig",
    description: "Fund management for startup/project",
    owners: [
      // Founders
      // "0x...",
      // "0x...",
      // Investors/Advisors
      // "0x...",
      // "0x..."
    ],
    requiredConfirmations: 2,
    safeModeEnabled: true,
    gnosisCompatibility: true,
    timelockEnabled: true,
    useCase: "project_funds",

    timelock: {
      minimumDelay: 12 * 60 * 60, // 12 hours
      maximumDelay: 7 * 24 * 60 * 60, // 7 days
      gracePeriod: 3 * 24 * 60 * 60, // 3 days

      tier1Threshold: "5", // 5 ETH
      tier2Threshold: "50", // 50 ETH

      tier1Confirmations: 2,
      tier2Confirmations: 3,
      tier3Confirmations: 4,

      emergencyDelay: 1 * 60 * 60, // 1 hour
      emergencyGracePeriod: 12 * 60 * 60 // 12 hours
    },

    timelockAdmins: [
      // "0x...",
      // "0x..."
    ]
  },

  // DeFi protocol governance (tier 2)
  defi: {
    name: "DeFi Protocol Governance",
    description: "Protocol governance with timelock and emergency controls",
    owners: [
      // Core team
      // "0x...",
      // "0x...",
      // Foundation
      // "0x...",
      // Community representatives
      // "0x...",
      // "0x..."
    ],
    requiredConfirmations: 3,
    safeModeEnabled: true,
    gnosisCompatibility: true,
    timelockEnabled: true,
    useCase: "defi_governance",

    timelock: {
      minimumDelay: 12 * 60 * 60, // 12 hours
      maximumDelay: 14 * 24 * 60 * 60, // 14 days
      gracePeriod: 7 * 24 * 60 * 60, // 7 days

      tier1Threshold: "100", // 100 ETH
      tier2Threshold: "1000", // 1000 ETH

      tier1Confirmations: 3,
      tier2Confirmations: 4,
      tier3Confirmations: 5,

      emergencyDelay: 2 * 60 * 60, // 2 hours
      emergencyGracePeriod: 48 * 60 * 60 // 48 hours
    },

    timelockAdmins: [
      // Core team members
      // "0x...",
      // "0x..."
    ],

    // Special permissions for protocol operations
    specialOperations: {
      // For pausing/unpausing protocol
      emergencyPause: {
        requiredConfirmations: 2,
        delay: 1 * 60 * 60 // 1 hour
      },
      // For changing protocol parameters
      parameterChange: {
        requiredConfirmations: 3,
        delay: 12 * 60 * 60 // 12 hours
      },
      // For upgrading contracts
      contractUpgrade: {
        requiredConfirmations: 4,
        delay: 48 * 60 * 60 // 48 hours
      }
    }
  },

  // Personal/Family multisig (tier 1)
  personal: {
    name: "Personal/Family Multisig",
    description: "Personal or family asset management",
    owners: [
      // Family members
      // "0x...",
      // "0x...",
      // "0x...",
      // "0x..."
    ],
    requiredConfirmations: 3,
    safeModeEnabled: true,
    gnosisCompatibility: true,
    timelockEnabled: false, // Optional for personal use
    useCase: "personal_assets",

    // Simplified settings for personal use
    simplified: {
      enableInheritance: true,
      emergencyContact: "0x...", // Backup person
      dailyLimit: "5", // 5 ETH per day
      weeklyLimit: "20" // 20 ETH per week
    }
  }
};
