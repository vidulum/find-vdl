import json
import math
from bech32 import bech32_decode, bech32_encode
from cosmos_sdk.core import AccAddress

with open("vdl-dump-13827200.json", encoding="utf8") as f:
    data = json.load(f)


class WalletManager:

    def __init__(self):
        self.wallets = {}

    def add_wallet(self, address):
        if address not in self.wallets:
            self.wallets[address] = {
                "balance_uvdl": 0,
                "staking_uvdl": 0,
                "redelegating_uvdl": 0,
                "unbonding_stake_uvdl": 0,
                "unclaimed_staking_rewards_uvdl": 0,
                "unclaimed_validator_rewards_uvdl": 0,
                "unclaimed_validator_commissions_uvdl": 0,
                "final_claim_uvdl": 0,
                "vdl_final_claim_balance": 0,
            }

    def get_all_wallets(self):
        return self.wallets

    def get_wallet(self, address):
        return self.wallets[address]

    def set_wallet_key(self, address, k, v):
        if address not in self.wallets:
            self.add_wallet(address)
        if k in self.wallets[address]:
            self.wallets[address][k] += v
        else:
            self.wallets[address][k] = v

    def update_balances(self):
        for address in self.wallets:
            self.wallets[address]["final_claim_uvdl"] = (
                self.wallets[address]["balance_uvdl"]
                + self.wallets[address]["staking_uvdl"]
                + self.wallets[address]["redelegating_uvdl"]
                + self.wallets[address]["unbonding_stake_uvdl"]
                + self.wallets[address]["unclaimed_staking_rewards_uvdl"]
                + self.wallets[address]["unclaimed_validator_rewards_uvdl"]
                + self.wallets[address]["unclaimed_validator_commissions_uvdl"]
            )
            self.wallets[address]["vdl_final_claim_balance"] = round(
                self.wallets[address]["final_claim_uvdl"] / 1000000, 6
            )


# Init Wallet Manager
wm = WalletManager()


# function that filters for uvdl
def find_uvdl(coins):
    res = list(filter(lambda c: c["denom"] == "uvdl", coins))
    if len(res) == 1:
        return res[0]["amount"]
    else:
        return False


def decode_validator_address(address):
    if address.startswith("vdl1"):
        return address
    else:
        vals = bech32_decode(address)
        if vals[1] is None:
            exit()
        return AccAddress(bech32_encode("vdl", vals[1]))


# Extract balances from different sections

# Section: bank -> balances
for balance in data["app_state"]["bank"]["balances"]:
    address = balance["address"]
    uvdl_only = find_uvdl(balance["coins"])

    if uvdl_only:
        wm.add_wallet(address)
        wm.set_wallet_key(address, "balance_uvdl", math.ceil(float(uvdl_only)))
        print(f"bank -> balances: {address}, balance_uvdl: {uvdl_only}")

# Section: staking -> delegations -> shares
for delegation in data["app_state"]["staking"]["delegations"]:
    address = delegation["delegator_address"]
    amount = float(delegation["shares"])
    if amount:
        wm.set_wallet_key(address, "staking_uvdl", math.ceil(amount))
        print(f"staking -> delegations: {address}, staking_uvdl: {amount}")

# Section: staking -> unbonding_delegations
for unbonding in data["app_state"]["staking"]["unbonding_delegations"]:
    address = unbonding["delegator_address"]
    amount = 0
    for entry in unbonding["entries"]:
        amount += float(entry["balance"])

    if amount:
        wm.set_wallet_key(address, "unbonding_stake_uvdl", math.ceil(amount))
        print(
            f"staking -> unbonding_delegations: {address}, unbonding_stake_uvdl: {amount}"
        )

# Section: staking -> redelegations
for redelegator in data["app_state"]["staking"]["redelegations"]:
    address = redelegator["delegator_address"]
    amount = 0
    for entry in redelegator["entries"]:
        amount += int(entry["initial_balance"])
    if amount:
        wm.set_wallet_key(address, "redelegating_uvdl", amount)
        print(f"staking -> redelegations: {address}, redelegating_uvdl: {amount}")

# Section: distribution -> outstanding_rewards
for outstanding_rewards in data["app_state"]["distribution"]["outstanding_rewards"]:
    uvdl_only = find_uvdl(outstanding_rewards["outstanding_rewards"])
    if uvdl_only:
        address = decode_validator_address(outstanding_rewards["validator_address"])
        amount = float(uvdl_only)
        wm.set_wallet_key(address, "unclaimed_staking_rewards_uvdl", math.ceil(amount))
        print(
            f"distribution -> outstanding_rewards: {address}, unclaimed_staking_rewards_uvdl: {amount}"
        )

# Section: distribution -> validator_accumulated_commissions
for commission in data["app_state"]["distribution"][
    "validator_accumulated_commissions"
]:
    uvdl_only = find_uvdl(commission["accumulated"]["commission"])
    if uvdl_only:
        address = decode_validator_address(commission["validator_address"])
        amount = float(uvdl_only)
        wm.set_wallet_key(
            address, "unclaimed_validator_commissions_uvdl", math.ceil(amount)
        )
        print(
            f"distribution -> validator_accumulated_commissions: {address}, unclaimed_validator_commissions_uvdl: {amount}"
        )

# Section: distribution -> validator_current_rewards
for reward in data["app_state"]["distribution"]["validator_current_rewards"]:
    uvdl_only = find_uvdl(reward["rewards"]["rewards"])
    if uvdl_only:
        address = decode_validator_address(reward["validator_address"])
        amount = float(uvdl_only)
        wm.set_wallet_key(
            address, "unclaimed_validator_rewards_uvdl", math.ceil(amount)
        )
        print(
            f"distribution -> validator_current_rewards: {address}, unclaimed_validator_rewards_uvdl: {amount}"
        )

# Update balance_uvdl to be the sum of all other fields
wm.update_balances()

# Export results
result = []
TOTAL_CLAIMABLE_VDL = 0
STAKING_VDL = 0
REDELEGATING_VDL = 0
UNBONDING_STAKE_VDL = 0
STAKING_REWARDS_VDL = 0
VALIDATOR_REWARDS_VDL = 0
VALIDATOR_COMMISSIONS_VDL = 0

wallets = wm.get_all_wallets()
for wallet in wallets:
    result.append({"address": wallet, **wallets[wallet]})

    # Calculate totals
    STAKING_VDL += wallets[wallet]["staking_uvdl"]
    REDELEGATING_VDL += wallets[wallet]["redelegating_uvdl"]
    UNBONDING_STAKE_VDL += wallets[wallet]["unbonding_stake_uvdl"]
    STAKING_REWARDS_VDL += wallets[wallet]["unclaimed_staking_rewards_uvdl"]
    VALIDATOR_REWARDS_VDL += wallets[wallet]["unclaimed_validator_rewards_uvdl"]
    VALIDATOR_COMMISSIONS_VDL += wallets[wallet]["unclaimed_validator_commissions_uvdl"]

# Calculate Balances VDL
BALANCES_VDL = (
    STAKING_VDL
    + REDELEGATING_VDL
    + UNBONDING_STAKE_VDL
    + STAKING_REWARDS_VDL
    + VALIDATOR_REWARDS_VDL
    + VALIDATOR_COMMISSIONS_VDL
)

# Calculate Total Claimable VDL
TOTAL_CLAIMABLE_VDL = (
    STAKING_VDL
    + REDELEGATING_VDL
    + UNBONDING_STAKE_VDL
    + STAKING_REWARDS_VDL
    + VALIDATOR_REWARDS_VDL
    + VALIDATOR_COMMISSIONS_VDL
    + BALANCES_VDL
)

STAKING = round(STAKING_VDL / 1000000, 6)
REDELEGATING = round(REDELEGATING_VDL / 1000000, 6)
UNBONDING = round(UNBONDING_STAKE_VDL / 1000000, 6)
STAKING_REWARDS = round(STAKING_REWARDS_VDL / 1000000, 6)
VALIDATOR_REWARDS = round(VALIDATOR_REWARDS_VDL / 1000000, 6)
VALIDATOR_COMMISSIONS = round(VALIDATOR_COMMISSIONS_VDL / 1000000, 6)
BALANCES = round(BALANCES_VDL / 1000000, 6)
TOTAL_CLAIMABLE = round(TOTAL_CLAIMABLE_VDL / 1000000, 6)

output_file = "all_vidulum-1_vdl.json"
L = [
    {"Total Claimable VDL": TOTAL_CLAIMABLE},
    {"Staking VDL": STAKING},
    {"Redelegating VDL": REDELEGATING},
    {"Unbonding Stake VDL": UNBONDING},
    {"Staking Rewards VDL": STAKING_REWARDS},
    {"Validator Rewards VDL": VALIDATOR_REWARDS},
    {"Validator Commissions VDL": VALIDATOR_COMMISSIONS},
    {"Balances VDL": BALANCES},
] + result

with open(output_file, "w") as f:
    json.dump(L, f, indent=2)

print(
    f"Results have been written to {output_file} with {len(result)} wallets balances found."
)
