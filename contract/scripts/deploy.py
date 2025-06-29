from ape import accounts, project


def main():
    acct = accounts.test_accounts[0]  # pre-funded local test account
    contract = acct.deploy(project.EDGChainE)
    print("Contract deployed at:", contract.address)
