import json, math
from bech32 import bech32_decode, bech32_encode
from cosmos_sdk.core import AccAddress

with open("vdl-dump-13827200.json", encoding="utf8") as f:
    data = json.load(f)


class WalletManager:

    def __init__(self):
        self.wallets = {}

    def add_wallet(self, address):
        wallet = {}
        wallet[address] = {}
        # print(self.wallets)
        # print(self.wallets["address"])
        wallet[address] = {
            "total_VDL": 0,
            "total_uvdl": 0,
            "balance_uvdl": 0,
            "staking_uvdl": 0,
            "redelegating_uvdl": 0,
            "unbonding_stake_uvdl": 0,
            "unclaimed_staking_rewards_uvdl": 0,
            "unclaimed_validator_rewards_uvdl": 0,
            "unclaimed_validator_commissions_uvdl": 0,
        }
        # print(wallet)
        self.wallets.update(wallet)
        # print(self.wallets)
        # if len(self.wallets) == 3:
        #     exit()

    def get_all_wallets(self):
        return self.wallets

    def get_wallet(self, address):
        return self.wallets[address]

    def set_wallet_key(self, address, k, v):
        if address not in self.wallets:
            self.add_wallet(address)
        self.wallets[address][k] = v

    def add_total_uvdl(self, address, amount):
        if address not in self.wallets:
            self.add_wallet(address)
        self.wallets[address]["total_uvdl"] += amount


# Init Wallet Manager
wm = WalletManager()


# function that filters for uvdl
def find_uvdl(coins):
    res = list(filter(lambda c: c["denom"] == "uvdl", coins))
    if len(res) == 1:
        if res[0]["denom"] != "uvdl":
            print("Error: (find_uvdl) uvdl not found")
        return res[0]["amount"]
    else:
        print("(find_uvdl) uvdl not found")
        return False


def decode_validator_address(address):
    if address[:4] == "vdl1":
        return address
    else:
        vals = bech32_decode(address)
        if vals[1] is None:
            exit()
        return AccAddress(bech32_encode("vdl", vals[1]))


# Extract balances from different sections

# balances include staking, rewards, commissions, and balances
# Section: bank -> balances
for balance in data["app_state"]["bank"]["balances"]:
    address = balance["address"]
    uvdl_only = find_uvdl(balance["coins"])

    if uvdl_only:
        wm.add_wallet(address)
        wm.set_wallet_key(address, "balance_uvdl", math.ceil(float(uvdl_only)))
        wm.add_total_uvdl(address, float(uvdl_only))
    else:
        print("Error: (bank -> balances) uvdl not found", balance)

# Section: staking -> delegations -> shares
for delegation in data["app_state"]["staking"]["delegations"]:
    address = delegation["delegator_address"]
    amount = float(delegation["shares"])
    if amount:
        wm.set_wallet_key(
            address,
            "staking_uvdl",
            math.ceil(amount),
        )
        wm.add_total_uvdl(address, amount)

# Section: staking -> unbonding_delegations
for unbonding in data["app_state"]["staking"]["unbonding_delegations"]:
    address = unbonding["delegator_address"]
    amount = 0
    for entry in unbonding["entries"]:
        amount += float(entry["balance"])

    if amount:
        wm.set_wallet_key(
            address,
            "unbonding_stake_uvdl",
            math.ceil(amount),
        )
        wm.add_total_uvdl(address, amount)

# redelegating stake
# Section: staking -> redelegations
for redelegator in data["app_state"]["staking"]["redelegations"]:
    address = redelegator["delegator_address"]
    amount = 0
    for entry in unbonding["entries"]:
        amount += float(entry["initial_balance"])

    if amount:
        wm.set_wallet_key(
            address,
            "redelegating_uvdl",
            math.ceil(amount),
        )
        wm.add_total_uvdl(address, amount)

# staking amount balances?
# for delegator in data["app_state"]["distribution"]["delegator_starting_infos"]:
#     address = delegator["delegator_address"]
#     amount = float(delegator["starting_info"]["stake"])
#     if amount:
#         wm.set_wallet_key(
#             address,
#             "staking_uvdl",
#             math.ceil(amount),
#         )
#         wm.add_total_uvdl(address, amount)

# Staking rewards
# Section: distribution -> outstanding_rewards
for outstanding_rewards in data["app_state"]["distribution"]["outstanding_rewards"]:
    uvdl_only = find_uvdl(outstanding_rewards["outstanding_rewards"])
    if uvdl_only:
        address = decode_validator_address(outstanding_rewards["validator_address"])
        amount = float(uvdl_only)
        wm.set_wallet_key(
            address,
            "unclaimed_staking_rewards_uvdl",
            math.ceil(amount),
        )
        wm.add_total_uvdl(address, amount)
    else:
        print(
            "Error: (distribution -> outstanding_rewards) uvdl not found",
            outstanding_rewards,
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
            address,
            "unclaimed_validator_commissions_uvdl",
            math.ceil(amount),
        )
        wm.add_total_uvdl(address, amount)
    else:
        print(
            "Error: (distribution -> validator_accumulated_commissions) uvdl not found",
            commission,
        )

# Section: distribution -> validator_current_rewards
for reward in data["app_state"]["distribution"]["validator_current_rewards"]:
    uvdl_only = find_uvdl(reward["rewards"]["rewards"])
    if uvdl_only:
        address = decode_validator_address(reward["validator_address"])
        amount = float(uvdl_only)
        wm.set_wallet_key(
            address,
            "unclaimed_validator_rewards_uvdl",
            math.ceil(amount),
        )
        wm.add_total_uvdl(address, amount)
    else:
        print(
            "Error: (distribution -> validator_current_rewards) uvdl not found",
            reward,
        )

# export results
result = []
TOTAL_VDL = 0
STAKING_VDL = 0
REDELEGATING_VDL = 0
UNBONDING_STAKE_VDL = 0
STAKING_REWARDS_VDL = 0
BALANCES_VDL = 0
VALIDATOR_REWARDS_VDL = 0
VALIDATOR_COMMISSIONS_VDL = 0

wallets = wm.get_all_wallets()
for wallet in wallets:
    total_uvdl = wallets[wallet]["total_uvdl"]
    wallets[wallet]["total_uvdl"] = math.ceil(total_uvdl)
    total_vdl = round(total_uvdl / 1000000, 6)
    wallets[wallet]["total_VDL"] = total_vdl
    result.append({"address": wallet, **wallets[wallet]})

    # Calculate totals
    STAKING_VDL += wallets[wallet]["staking_uvdl"]
    REDELEGATING_VDL += wallets[wallet]["redelegating_uvdl"]
    UNBONDING_STAKE_VDL += wallets[wallet]["unbonding_stake_uvdl"]
    STAKING_REWARDS_VDL = wallets[wallet]["unclaimed_staking_rewards_uvdl"]
    BALANCES_VDL += wallets[wallet]["balance_uvdl"]
    VALIDATOR_REWARDS_VDL += wallets[wallet]["unclaimed_validator_rewards_uvdl"]
    VALIDATOR_COMMISSIONS_VDL += wallets[wallet]["unclaimed_validator_commissions_uvdl"]

    TOTAL_VDL += total_vdl


STAKING = round(STAKING_VDL / 1000000, 6)
REDELEGATING = round(REDELEGATING_VDL / 1000000, 6)
UNBONDING = round(UNBONDING_STAKE_VDL / 1000000, 6)
BALANCES = round(BALANCES_VDL / 1000000, 6)
STAKING_REWARDS = round(STAKING_REWARDS_VDL / 1000000, 6)
VALIDATOR_REWARDS = round(VALIDATOR_REWARDS_VDL / 1000000, 6)
VALIDATOR_COMMISSIONS = round(VALIDATOR_COMMISSIONS_VDL / 1000000, 6)

output_file = "all_vidulum-1_vdl.json"
L = [
    {"Total VDL": TOTAL_VDL},
    {"Balances VDL": BALANCES},
    {"Staking VDL": STAKING},
    {"Redelegating VDL": REDELEGATING},
    {"Unbonding Stake VDL": UNBONDING},
    {"Staking Rewards VDL": STAKING_REWARDS},
    {"Validator Rewards VDL": VALIDATOR_REWARDS},
    {"Validator Commissions VDL": VALIDATOR_COMMISSIONS},
] + result


with open(output_file, "w") as f:
    json.dump(L, f, indent=2)

print(
    f"Results have been written to {output_file} with {len(result)} wallets balances found."
)
