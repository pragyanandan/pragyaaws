blockchain = [[1]]

def get_last_blockchain():
    return blockchain[-1]


def add_value (transaction_amount, last_transaction=[1]):
    blockchain.append([last_transaction,transaction_amount])

def get_user_input():
    return float(input ('your transaction amount '))


for x in range(1,4):
    tx_amount = get_user_input()
    add_value(last_transaction=get_last_blockchain(), transaction_amount=tx_amount)


print(tx_amount)

print (blockchain)