blockchain = [[1]]

def add_value (transaction_amount):
    blockchain.append([blockchain[-1],transaction_amount])
    print(blockchain)

add_value(78)
add_value(89)
add_value(90)