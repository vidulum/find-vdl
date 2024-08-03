import ijson
from collections import defaultdict

# Initialize a dictionary to store combined balances
combined_balances = defaultdict(lambda: {
    "balance_uvdl": 0,
    "liquidity_pool_balance_uvdl": 0,
    "final_claim_uvdl": 0,
    "vdl_final_claim_balance": 0
})

# Function to parse coins and add to combined balances
def add_balances(coins, address, key):
    for coin in coins:
        if coin['denom'] == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            combined_balances[address][key] += float(coin['amount'])

# File path for the large JSON file
input_file = 'dump_12819000_osmosis.json'

# Parse balances in 'bank' section incrementally
with open(input_file, 'r') as f:
    for prefix, event, value in ijson.parse(f):
        if prefix.endswith('.address') and event == 'string':
            address = value
        elif prefix.endswith('.coins.item.denom') and event == 'string':
            denom = value
        elif prefix.endswith('.coins.item.amount') and event == 'string' and denom == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            amount = float(value)
            combined_balances[address]['balance_uvdl'] += amount

# Parse liquidity pool balances in the specific liquidity pool incrementally
with open(input_file, 'r') as f:
    parser = ijson.parse(f)
    pool_found = False
    for prefix, event, value in parser:
        if prefix == 'app_state.gamm.pools.item.id' and event == 'string' and value == '613':
            pool_found = True
        elif pool_found and prefix.endswith('.tokens.item.denom') and event == 'string':
            denom = value
        elif pool_found and prefix.endswith('.tokens.item.amount') and event == 'string' and denom == 'ibc/E7B35499CFBEB0FF5778127ABA4FB2C4B79A6B8D3D831D4379C4048C238796BD':
            amount = float(value)
            address = prefix.split('.')[4]  # Assuming address can be inferred from the path for simplicity
            combined_balances[address]['liquidity_pool_balance_uvdl'] += amount
        elif pool_found and prefix == 'app_state.gamm.pools.item' and event == 'end_map':
            break

# Update the final_claim_uvdl and vdl_final_claim_balance
for address, balances in combined_balances.items():
    balances['final_claim_uvdl'] = balances['balance_uvdl'] + balances['liquidity_pool_balance_uvdl']
    balances['vdl_final_claim_balance'] = round(balances['final_claim_uvdl'] / 1000000, 6)

# Convert combined_balances dictionary to the desired output format
result = [{"address": address, **balances} for address, balances in combined_balances.items()]

# Calculate totals
TOTAL_CLAIMABLE_VDL = sum(balances['vdl_final_claim_balance'] for balances in combined_balances.values())
BALANCES_VDL = sum(balances['balance_uvdl'] for balances in combined_balances.values()) / 1000000
LIQUIDITY_POOL_BALANCES_VDL = sum(balances['liquidity_pool_balance_uvdl'] for balances in combined_balances.values()) / 1000000

# Prepare summary
summary = [
    {"Total Claimable VDL": TOTAL_CLAIMABLE_VDL},
    {"Balances VDL": BALANCES_VDL},
    {"Liquidity Pool Balances VDL": LIQUIDITY_POOL_BALANCES_VDL}
]

# Combine summary and result
output = summary + result

# Write the result to a file
output_file = 'osmosis-balances.json'
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f'Results have been written to {output_file}')
