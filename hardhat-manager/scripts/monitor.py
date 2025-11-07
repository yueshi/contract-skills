#!/usr/bin/env python3
"""
Smart Contract Monitoring and Alerting System

Real-time monitoring of smart contracts with configurable alerts
and notifications. Supports multiple networks and contract types.

Usage:
    python3 monitor.py --config <monitoring-config.json>
    python3 monitor.py --interactive
    python3 monitor.py --contract <address> --network <network>
"""

import os
import sys
import json
import time
import asyncio
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable


@dataclass
class Alert:
    """Alert data structure."""
    level: str  # info, warning, critical
    title: str
    message: str
    contract: str
    network: str
    timestamp: datetime
    data: dict


class SmartContractMonitor:
    def __init__(self):
        self.configs_dir = Path("configs")
        self.reports_dir = Path("monitoring-reports")
        self.logs_dir = Path("monitoring-logs")

        # Ensure directories exist
        self.configs_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        self.running = False
        self.contracts = []
        self.alerts = []
        self.network_configs = self.load_network_configs()

    def load_network_configs(self):
        """Load network configurations."""
        return {
            "ethereum": {
                "rpc": "https://mainnet.infura.io/v3/{INFURA_API_KEY}",
                "blockExplorer": "https://etherscan.io",
                "api": "https://api.etherscan.io/api"
            },
            "polygon": {
                "rpc": "https://polygon-rpc.com",
                "blockExplorer": "https://polygonscan.com",
                "api": "https://api.polygonscan.com/api"
            },
            "arbitrum": {
                "rpc": "https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}",
                "blockExplorer": "https://arbiscan.io",
                "api": "https://api.arbiscan.io/api"
            },
            "bsc": {
                "rpc": "https://bsc-dataseed1.binance.org",
                "blockExplorer": "https://bscscan.com",
                "api": "https://api.bscscan.com/api"
            },
            "goerli": {
                "rpc": "https://goerli.infura.io/v3/{INFURA_API_KEY}",
                "blockExplorer": "https://goerli.etherscan.io",
                "api": "https://api-goerli.etherscan.io/api"
            }
        }

    def create_monitoring_config(self, contract_address, network, contract_type="generic"):
        """Create a monitoring configuration template."""
        config = {
            "monitoring": {
                "contractAddress": contract_address,
                "network": network,
                "contractType": contract_type,
                "interval": 30,  # seconds
                "enabled": True,
                "createdAt": datetime.now().isoformat()
            },
            "alerts": {
                "email": {
                    "enabled": False,
                    "recipients": [],
                    "smtp": {
                        "server": "smtp.gmail.com",
                        "port": 587,
                        "username": "",
                        "password": ""
                    }
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                },
                "discord": {
                    "enabled": False,
                    "webhook": ""
                },
                "slack": {
                    "enabled": False,
                    "webhook": ""
                }
            },
            "metrics": {
                "balance": {
                    "enabled": True,
                    "thresholds": {
                        "min": 0.1,
                        "max": 1000
                    }
                },
                "transactions": {
                    "enabled": True,
                    "thresholds": {
                        "frequency": 10,  # alerts if more than 10 tx in 5 minutes
                        "timeWindow": 300
                    }
                },
                "gas": {
                    "enabled": True,
                    "thresholds": {
                        "max": 1000000  # alert if gas > 1M
                    }
                },
                "events": {
                    "enabled": True,
                    "monitoredEvents": ["Transfer", "Approval", "OwnershipTransferred"]
                },
                "errors": {
                    "enabled": True,
                    "monitoredErrors": ["reverted", "failed"]
                }
            }
        }

        # Add contract-specific monitoring
        if contract_type == "erc20":
            config["metrics"]["totalSupply"] = {"enabled": True}
            config["metrics"]["holders"] = {"enabled": True, "threshold": {"min": 10}}
        elif contract_type == "nft":
            config["metrics"]["totalSupply"] = {"enabled": True}
            config["metrics"]["minting"] = {"enabled": True, "threshold": {"max": 1000}}
        elif contract_type == "vault":
            config["metrics"]["tvl"] = {"enabled": True, "threshold": {"min": 1000}}
            config["metrics"]["apy"] = {"enabled": True}

        return config

    def save_config(self, config, filename=None):
        """Save monitoring configuration to file."""
        if filename is None:
            contract_name = config["monitoring"]["contractAddress"][:8]
            network = config["monitoring"]["network"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitor_{contract_name}_{network}_{timestamp}.json"

        config_file = self.configs_dir / filename
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Configuration saved to: {config_file}")
        return config_file

    def load_config(self, config_file):
        """Load monitoring configuration from file."""
        config_path = Path(config_file)
        if not config_path.exists():
            config_path = self.configs_dir / config_file

        with open(config_path, 'r') as f:
            config = json.load(f)

        print(f"✅ Configuration loaded from: {config_path}")
        return config

    def get_contract_balance(self, contract_address, network):
        """Get contract balance."""
        try:
            # This would use ethers.js or web3 to get balance
            # For now, return mock data
            return {
                "eth": float(time.time()) % 100,
                "usd": float(time.time()) % 10000
            }
        except Exception as e:
            return {"error": str(e)}

    def get_recent_transactions(self, contract_address, network, limit=10):
        """Get recent transactions for contract."""
        try:
            # This would query blockchain API
            # For now, return mock data
            transactions = []
            for i in range(limit):
                tx = {
                    "hash": f"0x{''.join(['0'] * 64)}",
                    "timestamp": datetime.now() - timedelta(minutes=i*5),
                    "from": f"0x{''.join(['1'] * 40)}",
                    "to": f"0x{''.join(['2'] * 40)}",
                    "value": float(time.time()) % 1000,
                    "gasUsed": int(time.time()) % 1000000
                }
                transactions.append(tx)
            return transactions
        except Exception as e:
            return {"error": str(e)}

    def get_contract_events(self, contract_address, network, event_types=None, limit=10):
        """Get recent events for contract."""
        try:
            # This would query blockchain API for events
            # For now, return mock data
            events = []
            for i in range(limit):
                event = {
                    "event": event_types[i % len(event_types)] if event_types else "Transfer",
                    "address": contract_address,
                    "blockNumber": int(time.time()) % 1000000,
                    "timestamp": datetime.now() - timedelta(minutes=i*2),
                    "returnValues": {
                        "from": f"0x{''.join(['3'] * 40)}",
                        "to": f"0x{''.join(['4'] * 40)}",
                        "value": int(time.time()) % 1000
                    }
                }
                events.append(event)
            return events
        except Exception as e:
            return {"error": str(e)}

    def check_balance_alerts(self, contract, config):
        """Check balance-related alerts."""
        alerts = []
        balance_data = self.get_contract_balance(contract["address"], contract["network"])

        if "error" in balance_data:
            return [Alert(
                level="critical",
                title="Balance Check Failed",
                message=f"Failed to get balance: {balance_data['error']}",
                contract=contract["address"],
                network=contract["network"],
                timestamp=datetime.now(),
                data=balance_data
            )]

        balance_config = config["metrics"]["balance"]
        if not balance_config["enabled"]:
            return alerts

        eth_balance = balance_data.get("eth", 0)
        thresholds = balance_config["thresholds"]

        if eth_balance < thresholds["min"]:
            alerts.append(Alert(
                level="warning",
                title="Low Balance",
                message=f"Contract balance is low: {eth_balance:.4f} ETH",
                contract=contract["address"],
                network=contract["network"],
                timestamp=datetime.now(),
                data={"balance": balance_data}
            ))

        if eth_balance > thresholds["max"]:
            alerts.append(Alert(
                level="info",
                title="High Balance",
                message=f"Contract balance is high: {eth_balance:.4f} ETH",
                contract=contract["address"],
                network=contract["network"],
                timestamp=datetime.now(),
                data={"balance": balance_data}
            ))

        return alerts

    def check_transaction_alerts(self, contract, config):
        """Check transaction-related alerts."""
        alerts = []
        tx_config = config["metrics"]["transactions"]

        if not tx_config["enabled"]:
            return alerts

        transactions = self.get_recent_transactions(
            contract["address"],
            contract["network"],
            limit=50
        )

        if "error" in transactions:
            return [Alert(
                level="critical",
                title="Transaction Check Failed",
                message=f"Failed to get transactions: {transactions['error']}",
                contract=contract["address"],
                network=contract["network"],
                timestamp=datetime.now(),
                data=transactions
            )]

        # Check transaction frequency
        now = datetime.now()
        time_window = tx_config["thresholds"]["timeWindow"]
        threshold = tx_config["thresholds"]["frequency"]

        recent_tx = [
            tx for tx in transactions
            if now - tx["timestamp"] < timedelta(seconds=time_window)
        ]

        if len(recent_tx) > threshold:
            alerts.append(Alert(
                level="warning",
                title="High Transaction Frequency",
                message=f"High transaction activity: {len(recent_tx)} transactions in {time_window}s",
                contract=contract["address"],
                network=contract["network"],
                timestamp=datetime.now(),
                data={
                    "transactionCount": len(recent_tx),
                    "timeWindow": time_window,
                    "transactions": recent_tx[:5]  # Limit data size
                }
            ))

        # Check for high gas usage
        gas_threshold = config["metrics"]["gas"]["thresholds"]["max"]
        for tx in recent_tx:
            if tx["gasUsed"] > gas_threshold:
                alerts.append(Alert(
                    level="info",
                    title="High Gas Usage",
                    message=f"Transaction used high gas: {tx['gasUsed']:,}",
                    contract=contract["address"],
                    network=contract["network"],
                    timestamp=datetime.now(),
                    data={
                        "transactionHash": tx["hash"],
                        "gasUsed": tx["gasUsed"],
                        "timestamp": tx["timestamp"]
                    }
                ))

        return alerts

    def check_event_alerts(self, contract, config):
        """Check event-related alerts."""
        alerts = []
        event_config = config["metrics"]["events"]

        if not event_config["enabled"]:
            return alerts

        monitored_events = event_config["monitoredEvents"]
        events = self.get_contract_events(
            contract["address"],
            contract["network"],
            monitored_events,
            limit=20
        )

        if "error" in events:
            return [Alert(
                level="critical",
                title="Event Check Failed",
                message=f"Failed to get events: {events['error']}",
                contract=contract["address"],
                network=contract["network"],
                timestamp=datetime.now(),
                data=events
            )]

        # Generate alerts for monitored events
        for event in events:
            if event["event"] in monitored_events:
                alerts.append(Alert(
                    level="info",
                    title=f"Event: {event['event']}",
                    message=f"Contract emitted {event['event']} event",
                    contract=contract["address"],
                    network=contract["network"],
                    timestamp=datetime.now(),
                    data=event
                ))

        return alerts

    def check_contract_health(self, contract, config):
        """Check overall contract health."""
        alerts = []

        # Combine all alert checks
        alerts.extend(self.check_balance_alerts(contract, config))
        alerts.extend(self.check_transaction_alerts(contract, config))
        alerts.extend(self.check_event_alerts(contract, config))

        return alerts

    def send_alert(self, alert, config):
        """Send alert through configured channels."""
        print(f"🚨 {alert.level.upper()}: {alert.title}")
        print(f"   Contract: {alert.contract} ({alert.network})")
        print(f"   Message: {alert.message}")
        print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Store alert
        self.alerts.append(alert)

        # Send to configured channels
        alert_config = config["alerts"]

        if alert_config["email"]["enabled"]:
            self.send_email_alert(alert, alert_config["email"])

        if alert_config["webhook"]["enabled"]:
            self.send_webhook_alert(alert, alert_config["webhook"])

        if alert_config["discord"]["enabled"]:
            self.send_discord_alert(alert, alert_config["discord"])

        if alert_config["slack"]["enabled"]:
            self.send_slack_alert(alert, alert_config["slack"])

    def send_email_alert(self, alert, email_config):
        """Send email alert."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = email_config["smtp"]["username"]
            msg['To'] = ", ".join(email_config["recipients"])
            msg['Subject'] = f"[{alert.level.upper()}] {alert.title}"

            body = f"""
Contract: {alert.contract}
Network: {alert.network}
Level: {alert.level}
Message: {alert.message}
Time: {alert.timestamp}

Data: {json.dumps(alert.data, indent=2)}
"""

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(email_config["smtp"]["server"], email_config["smtp"]["port"])
            server.starttls()
            server.login(email_config["smtp"]["username"], email_config["smtp"]["password"])
            server.send_message(msg)
            server.quit()

            print(f"📧 Email alert sent to {len(email_config['recipients'])} recipients")

        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")

    def send_webhook_alert(self, alert, webhook_config):
        """Send webhook alert."""
        try:
            payload = {
                "level": alert.level,
                "title": alert.title,
                "message": alert.message,
                "contract": alert.contract,
                "network": alert.network,
                "timestamp": alert.timestamp.isoformat(),
                "data": alert.data
            }

            headers = webhook_config.get("headers", {})
            headers["Content-Type"] = "application/json"

            response = requests.post(
                webhook_config["url"],
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                print(f"🌐 Webhook alert sent successfully")
            else:
                print(f"❌ Webhook alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Failed to send webhook alert: {e}")

    def send_discord_alert(self, alert, discord_config):
        """Send Discord alert."""
        try:
            payload = {
                "embeds": [{
                    "title": f"[{alert.level.upper()}] {alert.title}",
                    "description": alert.message,
                    "color": self.get_discord_color(alert.level),
                    "fields": [
                        {"name": "Contract", "value": f"`{alert.contract}`", "inline": True},
                        {"name": "Network", "value": alert.network, "inline": True},
                        {"name": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "inline": True}
                    ],
                    "timestamp": alert.timestamp.isoformat()
                }]
            }

            response = requests.post(discord_config["webhook"], json=payload, timeout=10)

            if response.status_code == 204:
                print(f"💬 Discord alert sent successfully")
            else:
                print(f"❌ Discord alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Failed to send Discord alert: {e}")

    def send_slack_alert(self, alert, slack_config):
        """Send Slack alert."""
        try:
            payload = {
                "text": f"[{alert.level.upper()}] {alert.title}",
                "attachments": [{
                    "color": self.get_slack_color(alert.level),
                    "fields": [
                        {"title": "Contract", "value": f"`{alert.contract}`", "short": True},
                        {"title": "Network", "value": alert.network, "short": True},
                        {"title": "Message", "value": alert.message, "short": False}
                    ],
                    "ts": int(alert.timestamp.timestamp())
                }]
            }

            response = requests.post(slack_config["webhook"], json=payload, timeout=10)

            if response.status_code == 200:
                print(f"📱 Slack alert sent successfully")
            else:
                print(f"❌ Slack alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Failed to send Slack alert: {e}")

    def get_discord_color(self, level):
        """Get Discord embed color for alert level."""
        colors = {
            "info": 3447003,    # Blue
            "warning": 16312092,  # Orange
            "critical": 15158332  # Red
        }
        return colors.get(level, 3447003)

    def get_slack_color(self, level):
        """Get Slack attachment color for alert level."""
        colors = {
            "info": "#36a64f",      # Green
            "warning": "#ff9500",   # Orange
            "critical": "#ff0000"    # Red
        }
        return colors.get(level, "#36a64f")

    def log_alert(self, alert):
        """Log alert to file."""
        log_file = self.logs_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"

        with open(log_file, 'a') as f:
            log_entry = f"{alert.timestamp.isoformat()} [{alert.level.upper()}] {alert.title} - {alert.message} ({alert.contract} on {alert.network})\n"
            f.write(log_entry)

    def generate_monitoring_report(self):
        """Generate monitoring report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"monitoring_report_{timestamp}.json"

        report = {
            "summary": {
                "totalAlerts": len(self.alerts),
                "infoAlerts": len([a for a in self.alerts if a.level == "info"]),
                "warningAlerts": len([a for a in self.alerts if a.level == "warning"]),
                "criticalAlerts": len([a for a in self.alerts if a.level == "critical"]),
                "monitoredContracts": len(self.contracts),
                "timestamp": datetime.now().isoformat()
            },
            "alerts": [
                {
                    "level": alert.level,
                    "title": alert.title,
                    "message": alert.message,
                    "contract": alert.contract,
                    "network": alert.network,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in self.alerts[-100:]  # Last 100 alerts
            ],
            "contracts": self.contracts
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📊 Monitoring report saved to: {report_file}")
        return report_file

    def start_monitoring(self, config):
        """Start monitoring contract."""
        print(f"🔍 Starting monitoring for {config['monitoring']['contractAddress']} on {config['monitoring']['network']}")
        print(f"   Interval: {config['monitoring']['interval']} seconds")
        print(f"   Press Ctrl+C to stop monitoring")
        print()

        contract = {
            "address": config["monitoring"]["contractAddress"],
            "network": config["monitoring"]["network"],
            "type": config["monitoring"]["contractType"]
        }

        self.contracts.append(contract)
        self.running = True

        try:
            while self.running:
                # Check contract health
                alerts = self.check_contract_health(contract, config)

                # Send alerts
                for alert in alerts:
                    self.send_alert(alert, config)
                    self.log_alert(alert)

                # Wait for next interval
                time.sleep(config["monitoring"]["interval"])

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            self.running = False

        # Generate final report
        self.generate_monitoring_report()

    def interactive_mode(self):
        """Interactive monitoring setup."""
        print("🎯 Interactive Contract Monitoring Setup")
        print("="*50)

        # Contract address
        while True:
            contract_address = input("\nEnter contract address: ").strip()
            if contract_address.startswith("0x") and len(contract_address) == 42:
                break
            print("Invalid contract address format")

        # Network selection
        print("\nAvailable networks:")
        network_list = list(self.network_configs.keys())
        for i, network in enumerate(network_list, 1):
            print(f"{i}. {network}")

        while True:
            try:
                choice = input(f"Select network (1-{len(network_list)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(network_list):
                    break
                print("Invalid choice")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled")
                return

        selected_network = network_list[int(choice) - 1]

        # Contract type
        print("\nContract types:")
        print("1. ERC20 Token")
        print("2. ERC721 NFT")
        print("3. DeFi Vault")
        print("4. Generic")

        while True:
            try:
                type_choice = input("Select contract type (1-4): ").strip()
                if type_choice in ["1", "2", "3", "4"]:
                    break
                print("Invalid choice")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled")
                return

        contract_types = {"1": "erc20", "2": "nft", "3": "vault", "4": "generic"}
        contract_type = contract_types[type_choice]

        # Monitoring interval
        while True:
            try:
                interval = input("Monitoring interval in seconds (default: 30): ").strip()
                if not interval:
                    interval = 30
                else:
                    interval = int(interval)
                if interval > 0:
                    break
                print("Interval must be positive")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Operation cancelled")
                return

        # Create configuration
        config = self.create_monitoring_config(contract_address, selected_network, contract_type)
        config["monitoring"]["interval"] = interval

        # Alert configuration
        print("\nConfigure alerts (optional, press Enter to skip):")

        email_enabled = input("Enable email alerts? (y/N): ").strip().lower()
        if email_enabled == 'y':
            config["alerts"]["email"]["enabled"] = True
            recipients = input("Email recipients (comma-separated): ").strip()
            config["alerts"]["email"]["recipients"] = [r.strip() for r in recipients.split(",")]

        webhook_enabled = input("Enable webhook alerts? (y/N): ").strip().lower()
        if webhook_enabled == 'y':
            config["alerts"]["webhook"]["enabled"] = True
            webhook_url = input("Webhook URL: ").strip()
            config["alerts"]["webhook"]["url"] = webhook_url

        # Save configuration
        config_file = self.save_config(config)
        print(f"\n✅ Configuration saved to: {config_file}")

        # Start monitoring
        confirm = input(f"\n🚀 Start monitoring {contract_address} on {selected_network}? (y/N): ").strip().lower()
        if confirm == 'y':
            self.start_monitoring(config)
        else:
            print("❌ Monitoring cancelled")


def main():
    parser = argparse.ArgumentParser(description="Smart contract monitoring and alerting")
    parser.add_argument("--config", help="Monitoring configuration file")
    parser.add_argument("--contract", help="Contract address to monitor")
    parser.add_argument("--network", help="Network name")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--list-networks", action="store_true", help="List available networks")

    args = parser.parse_args()

    monitor = SmartContractMonitor()

    if args.list_networks:
        print("Available networks:")
        for network, config in monitor.network_configs.items():
            print(f"  {network}: {config['rpc']}")
        return

    if args.interactive:
        monitor.interactive_mode()
    elif args.config:
        try:
            config = monitor.load_config(args.config)
            monitor.start_monitoring(config)
        except Exception as e:
            print(f"❌ Monitoring failed: {e}")
    elif args.contract and args.network:
        config = monitor.create_monitoring_config(args.contract, args.network)
        config_file = monitor.save_config(config)
        monitor.start_monitoring(config)
    else:
        print("❌ Please provide --config file, --contract and --network, or use --interactive mode")
        parser.print_help()


if __name__ == "__main__":
    main()