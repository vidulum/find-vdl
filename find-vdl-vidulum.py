# Run in virtual environment
# -->  source venv/bin/activate

import json
import math

from bech32 import bech32_decode, bech32_encode
from cosmos_sdk.core import AccAddress

with open("vdl-dump-13827200.json", encoding="utf8") as f:
    data = json.load(f)


class WalletManager:

    def __init__(self):
        self.wallets = {}
        self.validators = {}

    def add_wallet(self, address):
        if address not in self.wallets:
            self.wallets[address] = {
                "bank_balance_uvdl": 0,
                "staking_uvdl": [],
                "staking_balance_uvdl": 0,
                "unbonding_stake_uvdl": 0,
                # "redelegating_uvdl": 0,
                "unclaimed_staking_rewards_uvdl": 0,
                # "unclaimed_validator_rewards_uvdl": 0,
                # "unclaimed_validator_commissions_uvdl": 0,
                "final_claim_uvdl": 0,
                "vdl_final_claim_balance": 0,
            }

    def get_all_wallets(self):
        return self.wallets

    def get_all_validators(self):
        return self.validators

    def get_wallet(self, address):
        return self.wallets[address]

    def set_wallet_key(self, address, k, v):
        if address not in self.wallets:
            self.add_wallet(address)
        if k in self.wallets[address]:
            self.wallets[address][k] += v
        else:
            self.wallets[address][k] = v

    def add_delegation(self, address, delegation):
        if address not in self.wallets:
            self.add_wallet(address)
        self.wallets[address]["staking_uvdl"].append(delegation)

    def add_validator(self, validator):
        self.validators[validator["operator_address"]] = validator

    def get_validator_data(self, operator_address):
        return self.validators[operator_address]

    def update_balances(self):
        # all_validators = self.get_all_validators()
        # print(all_validators)
        for address in self.wallets:
            total_staking_balances = 0
            for staking_uvdl in self.wallets[address]["staking_uvdl"]:
                total_staking_balances += float(staking_uvdl["uvdl"])

            # if total_staking_balances > 0:
            #     print(
            #         f"address: {address}, staking_uvdl: {str(total_staking_balances)}"
            #     )

            self.wallets[address]["staking_balance_uvdl"] = total_staking_balances
            wallet = self.wallets[address]

            self.wallets[address]["final_claim_uvdl"] = (
                self.wallets[address]["bank_balance_uvdl"]
                + wallet["staking_balance_uvdl"]
                + wallet["unbonding_stake_uvdl"]
                # + wallet["redelegating_uvdl"]
                + wallet["unclaimed_staking_rewards_uvdl"]
                # + wallet["unclaimed_validator_rewards_uvdl"]
                # + wallet["unclaimed_validator_commissions_uvdl"]
            )

            self.wallets[address]["vdl_final_claim_balance"] = round(
                self.wallets[address]["final_claim_uvdl"] / 1000000, 6
            )

            # if self.wallets[address]["vdl_final_claim_balance"] > 1000000:
            #     print(
            #         f"address: {address}, claim_vdl: {self.wallets[address]["vdl_final_claim_balance"]}"
            #     )


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


def address_is_module(address, amount=None):
    if address in moduleAccounts:
        print(
            f"(MODULE ACCOUNT):{moduleNames[moduleAccounts.index(address)]} -> {address} -> {amount}"
        )
        return True
    else:
        return False


# List module accounts
moduleAccounts = [
    "vdl1yl6hdjhmkf37639730gffanpzndzdpmhtmxw69",  # "transfer"
    "vdl1fl48vsnmsdzcv85q5d2q4z5ajdha8yu3sleg53",  # "bonded_tokens_pool"
    "vdl1tygms3xhhs3yv487phx3dw4a95jn7t7lyl9ez9",  # "not_bonded_tokens_pool"
    "vdl10d07y265gmmuvt4z0w9aw880jnsr700jlxrzm4",  # "gov"
    "vdl1jv65s3grqf6v6jl3dp4t6c9t9rk99cd8zm5mye",  # "distribution"
    "vdl1m3h30wlvsf8llruxtpukdvsy0km2kum8d4hl2x",  # "mint"
    "vdl17xpfvakm2amg962yls6f84z3kell8c5l4an8xm",  # "fee_collector"
    "vdl1a53udazy8ayufvy0s434pfwjcedzqv34ngjzxg",  # "osmosis ibc escrow"
    "vdl1qyx9s8senm423qvfwh90h9ucymf6mxm627hly0",  # "archway ibc escrow"
]

moduleNames = [
    "transfer",
    "bonded_tokens_pool",
    "not_bonded_tokens_pool",
    "gov",
    "distribution",
    "mint",
    "fee_collector",
    "osmosis ibc escrow",
    "archway ibc escrow",
]


# Section: bank -> balances
for balance in data["app_state"]["bank"]["balances"]:
    address = balance["address"]

    uvdl_only = find_uvdl(balance["coins"])
    if address_is_module(address, uvdl_only):
        continue
    if uvdl_only:
        wm.add_wallet(address)
        wm.set_wallet_key(address, "bank_balance_uvdl", float(uvdl_only))
        # print(f"bank -> balances: {address}, balance_uvdl: {uvdl_only}")


# Need Validator Set and its data
# Section: staking -> validators
for validator in data["app_state"]["staking"]["validators"]:
    wm.add_validator(
        {
            "operator_address": validator["operator_address"],
            "decoded_operator_address": decode_validator_address(
                validator["operator_address"]
            ),
            "moniker": validator["description"]["moniker"],
            "total_shares": validator["delegator_shares"],
            "total_tokens": validator["tokens"],
        },
    )
    # print(f"{validator["operator_address"]}")


# Section: staking -> delegations -> shares
for delegation in data["app_state"]["staking"]["delegations"]:
    address = delegation["delegator_address"]

    validator_address = delegation["validator_address"]

    # Tokens per Share = validator.Tokens() / validatorShares()
    validator = wm.get_validator_data(validator_address)
    totalTokens = validator["total_tokens"]
    totalShares = validator["total_shares"]
    tokensPerShare = float(totalTokens) / float(totalShares)
    amount = float(delegation["shares"]) * tokensPerShare

    if address_is_module(address, amount):
        continue

    if amount:
        wm.add_delegation(
            address,
            {
                "moniker": validator["moniker"],
                "operator_address": validator_address,
                "uvdl": amount,
            },
        )
        # print(f"staking -> delegations: {address}, shares: {amount}")

# Section: staking -> unbonding_delegations
for unbonding in data["app_state"]["staking"]["unbonding_delegations"]:
    address = unbonding["delegator_address"]
    amount = 0
    for entry in unbonding["entries"]:
        amount += float(entry["balance"])

    if address_is_module(address, amount):
        continue

    if amount:
        wm.set_wallet_key(address, "unbonding_stake_uvdl", amount)
        # print(
        #     f"staking -> unbonding_delegations: {address}, unbonding_stake_uvdl: {amount}"
        # )

# These amounts are included in staking balances
# # Section: staking -> redelegations
# for redelegator in data["app_state"]["staking"]["redelegations"]:
#     address = redelegator["delegator_address"]
#     amount = 0
#     for entry in redelegator["entries"]:
#         amount += float(entry["initial_balance"])

#     if address_is_module(address, amount):
#         continue

#     if amount:
#         wm.set_wallet_key(address, "redelegating_uvdl", amount)
#         # print(f"staking -> redelegations: {address}, redelegating_uvdl: {amount}")


# Section: distribution -> outstanding_rewards
for outstanding_rewards in data["app_state"]["distribution"]["outstanding_rewards"]:
    uvdl_only = find_uvdl(outstanding_rewards["outstanding_rewards"])
    if uvdl_only:
        address = decode_validator_address(outstanding_rewards["validator_address"])
        if address_is_module(address, uvdl_only):
            continue
        amount = float(uvdl_only)
        wm.set_wallet_key(address, "unclaimed_staking_rewards_uvdl", amount)
        # print(
        #     f"distribution -> outstanding_rewards: {address}, unclaimed_staking_rewards_uvdl: {amount}"
        # )

# These amounts are included in Outstanding Rewards balances
# # Section: distribution -> validator_accumulated_commissions
# for commission in data["app_state"]["distribution"][
#     "validator_accumulated_commissions"
# ]:
#     uvdl_only = find_uvdl(commission["accumulated"]["commission"])
#     if uvdl_only:
#         address = decode_validator_address(commission["validator_address"])
#         if address_is_module(address, uvdl_only):
#             continue
#         amount = float(uvdl_only)
#         wm.set_wallet_key(address, "unclaimed_validator_commissions_uvdl", amount)
#         # print(
#         #     f"distribution -> validator_accumulated_commissions: {address}, unclaimed_validator_commissions_uvdl: {amount}"
#         # )

# These amounts are included in Outstanding Rewards balances
# # Section: distribution -> validator_current_rewards
# for reward in data["app_state"]["distribution"]["validator_current_rewards"]:
#     uvdl_only = find_uvdl(reward["rewards"]["rewards"])
#     if uvdl_only:
#         address = decode_validator_address(reward["validator_address"])
#         if address_is_module(address, uvdl_only):
#             continue
#         amount = float(uvdl_only)
#         wm.set_wallet_key(address, "unclaimed_validator_rewards_uvdl", amount)
#         # print(
#         #     f"distribution -> validator_current_rewards: {address}, unclaimed_validator_rewards_uvdl: {amount}"
#         # )

# Update bank_balance_uvdl to be the sum of all other fields
wm.update_balances()

# Export results
result = []
TOTAL_CLAIMABLE_VDL = 0
BALANCES_VDL = 0
STAKING_VDL = 0
# REDELEGATING_VDL = 0
UNBONDING_STAKE_VDL = 0
OUTSTANDING_REWARDS_VDL = 0
# VALIDATOR_REWARDS_VDL = 0
# VALIDATOR_COMMISSIONS_VDL = 0

wallets = wm.get_all_wallets()
validators = wm.get_all_validators()

for wallet in wallets:
    result.append({"address": wallet, **wallets[wallet]})

    # Calculate totals and add detailed debugging
    TOTAL_CLAIMABLE_VDL += wallets[wallet]["final_claim_uvdl"]
    BALANCES_VDL += wallets[wallet]["bank_balance_uvdl"]
    STAKING_VDL += wallets[wallet]["staking_balance_uvdl"]
    # REDELEGATING_VDL += wallets[wallet]["redelegating_uvdl"]
    UNBONDING_STAKE_VDL += wallets[wallet]["unbonding_stake_uvdl"]
    OUTSTANDING_REWARDS_VDL += wallets[wallet]["unclaimed_staking_rewards_uvdl"]
    # VALIDATOR_REWARDS_VDL += wallets[wallet]["unclaimed_validator_rewards_uvdl"]
    # VALIDATOR_COMMISSIONS_VDL += wallets[wallet]["unclaimed_validator_commissions_uvdl"]


BALANCES = round(BALANCES_VDL / 1000000, 6)
STAKING = round(STAKING_VDL / 1000000, 6)
# REDELEGATING = round(REDELEGATING_VDL / 1000000, 6)
UNBONDING = round(UNBONDING_STAKE_VDL / 1000000, 6)
OUTSTANDING_REWARDS = round(OUTSTANDING_REWARDS_VDL / 1000000, 6)
# VALIDATOR_REWARDS = round(VALIDATOR_REWARDS_VDL / 1000000, 6)
# VALIDATOR_COMMISSIONS = round(VALIDATOR_COMMISSIONS_VDL / 1000000, 6)
TOTAL_CLAIMABLE = round(TOTAL_CLAIMABLE_VDL / 1000000, 6)

output_file = "all_vidulum-1_vdl.json"
L = [
    {"Total Claimable VDL": TOTAL_CLAIMABLE},
    {"Total Balances VDL": BALANCES},
    {"Total Staking VDL": STAKING},
    {"Total Unbonding VDL": UNBONDING},
    # {"Redelegating VDL": REDELEGATING},
    {"Total Outstanding Rewards VDL": OUTSTANDING_REWARDS},
    # {"Validator Rewards VDL": VALIDATOR_REWARDS},
    # {"Validator Commissions VDL": VALIDATOR_COMMISSIONS},
] + result

with open(output_file, "w") as f:
    json.dump(L, f, indent=2)

EXPECTED_CLAIMABLE_VDL = (
    25366794.399120 - 507105.576038 - 1048214.719672 - 415322.582098
)

print(f"VDL TOTAL SUPPLY:   25,366,794.399120")
print(f"Community Pool:        -507,105.576038")
print(f"Osmosis uVDL supply: -1,048,214.719672")
print(f"Archway uVDL supply:   -415,322.582098")
print(f"Expected Claimable VDL:  {EXPECTED_CLAIMABLE_VDL}")
print("---------------------------------------------")
print(f"Total Claimable VDL: {TOTAL_CLAIMABLE}")
# print(f"Diff {EXPECTED_CLAIMABLE_VDL - TOTAL_CLAIMABLE}")
print("---------------------------------------------")
print(f"Balances VDL: {BALANCES}")
print(f"Staking VDL: {STAKING}")
print(f"Unbonding VDL: {UNBONDING}")
# print(f"Redelegating VDL: {REDELEGATING}")
print(f"Outstanding Rewards VDL: {OUTSTANDING_REWARDS}")
# print(f"Validator Rewards VDL: {VALIDATOR_REWARDS}")
# print(f"Validator Commissions VDL: {VALIDATOR_COMMISSIONS}")
print(
    f"Results have been written to {output_file} with {len(result)} wallets balances found."
)
