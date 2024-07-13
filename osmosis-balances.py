import ijson
import json
from collections import defaultdict

# Initialize a dictionary to store combined balances
combined_balances = defaultdict(float)

# Function to parse coins and add to combined balances
def add_balances(coins, address):
    for coin in coins:
        if coin['denom'] == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            combined_balances[address] += float(coin['amount'])

# File path for the large JSON file
input_file = '../osmosis-dump.json'

# Open the JSON file and use ijson to parse it incrementally
with open(input_file, 'r') as f:
    address = None
    denom = None
    amount = None
    # Parse balances in 'bank' section
    for prefix, event, value in ijson.parse(f):
        if (prefix, event) == ('app_state.bank.balances.item.address', 'string'):
            address = value
        elif (prefix, event) == ('app_state.bank.balances.item.coins.item.denom', 'string'):
            denom = value
        elif (prefix, event) == ('app_state.bank.balances.item.coins.item.amount', 'string') and denom == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            amount = float(value)
            combined_balances[address] += amount

# Reset the file pointer to the beginning of the file for the next section
with open(input_file, 'r') as f:
    address = None
    denom = None
    amount = None
    # Parse rewards in 'distribution' section
    for prefix, event, value in ijson.parse(f):
        if (prefix, event) == ('app_state.distribution.outstanding_rewards.item.validator_address', 'string'):
            address = value
        elif (prefix, event) == ('app_state.distribution.outstanding_rewards.item.outstanding_rewards.item.denom', 'string'):
            denom = value
        elif (prefix, event) == ('app_state.distribution.outstanding_rewards.item.outstanding_rewards.item.amount', 'string') and denom == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            amount = float(value)
            combined_balances[address] += amount

# Reset the file pointer to the beginning of the file for the next section
with open(input_file, 'r') as f:
    address = None
    denom = None
    amount = None
    # Parse commissions in 'distribution' section
    for prefix, event, value in ijson.parse(f):
        if (prefix, event) == ('app_state.distribution.validator_accumulated_commissions.item.validator_address', 'string'):
            address = value
        elif (prefix, event) == ('app_state.distribution.validator_accumulated_commissions.item.accumulated.commission.item.denom', 'string'):
            denom = value
        elif (prefix, event) == ('app_state.distribution.validator_accumulated_commissions.item.accumulated.commission.item.amount', 'string') and denom == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            amount = float(value)
            combined_balances[address] += amount

# Reset the file pointer to the beginning of the file for the next section
with open(input_file, 'r') as f:
    address = None
    denom = None
    amount = None
    # Parse current rewards in 'distribution' section
    for prefix, event, value in ijson.parse(f):
        if (prefix, event) == ('app_state.distribution.validator_current_rewards.item.validator_address', 'string'):
            address = value
        elif (prefix, event) == ('app_state.distribution.validator_current_rewards.item.rewards.rewards.item.denom', 'string'):
            denom = value
        elif (prefix, event) == ('app_state.distribution.validator_current_rewards.item.rewards.rewards.item.amount', 'string') and denom == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            amount = float(value)
            combined_balances[address] += amount

# Convert combined_balances dictionary to the desired output format
result = [{"address": address, "balance": balance} for address, balance in combined_balances.items()]

# Write the result to a file
output_file = 'osmosis-balances.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f'Results have been written to {output_file}')
