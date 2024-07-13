import json
from collections import defaultdict

with open('vdl-dump.json', encoding='utf8') as f:
    data = json.load(f)

combined_balances = defaultdict(float)

def add_balances(coins, address):
    for coin in coins:
        if coin['denom'] == 'uvdl':
            combined_balances[address] += float(coin['amount'])

# Extract balances from different sections
# Section: bank -> balances
for balance in data['app_state']['bank']['balances']:
    address = balance['address']
    coins = balance['coins']
    add_balances(coins, address)

# Section: distribution -> outstanding_rewards
for reward in data['app_state']['distribution']['outstanding_rewards']:
    coins = reward['outstanding_rewards']
    add_balances(coins, reward['validator_address'])

# Section: distribution -> validator_accumulated_commissions
for commission in data['app_state']['distribution']['validator_accumulated_commissions']:
    coins = commission['accumulated']['commission']
    add_balances(coins, commission['validator_address'])

# Section: distribution -> validator_current_rewards
for reward in data['app_state']['distribution']['validator_current_rewards']:
    coins = reward['rewards']['rewards']
    add_balances(coins, reward['validator_address'])

result = [{"address": address, "balance": balance} for address, balance in combined_balances.items()]

output_file = 'balances.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f'Results have been written to {output_file}')
