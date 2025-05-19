import argparse
import base64
import json
import pxsol
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--net', type=str, choices=['develop', 'mainnet', 'testnet'], default='develop')
parser.add_argument('--prikey', type=str, default='11111111111111111111111111111112')
parser.add_argument('args', nargs='+')
args = parser.parse_args()

if args.net == 'develop':
    pxsol.config.current = pxsol.config.develop
if args.net == 'mainnet':
    pxsol.config.current = pxsol.config.mainnet
if args.net == 'testnet':
    pxsol.config.current = pxsol.config.testnet
pxsol.config.current.log = 1


def call(c: str):
    return subprocess.run(c, check=True, shell=True)


def info_save(k: str, v: str) -> None:
    with open('res/info.json', 'r') as f:
        info = json.load(f)
    info[k] = v
    with open('res/info.json', 'w') as f:
        json.dump(info, f, indent=4)


def info_load(k: str) -> str:
    with open('res/info.json', 'r') as f:
        info = json.load(f)
    return info[k]


def deploy():
    # Deploy program
    user = pxsol.wallet.Wallet(pxsol.core.PriKey.base58_decode(args.prikey))
    call('cargo build-sbf -- -Znext-lockfile-bump')
    pxsol.log.debugln(f'main: deploy program')
    with open('target/deploy/pxsol_ss.so', 'rb') as f:
        data = bytearray(f.read())
    prog = user.program_deploy(data)
    pxsol.log.debugln(f'main: deploy program pubkey={prog}')
    info_save('pubkey', prog.base58())


def hi():
    user = pxsol.wallet.Wallet(pxsol.core.PriKey.base58_decode(args.prikey))
    prog = pxsol.core.PubKey(pxsol.base58.decode(info_load('pubkey')))
    rq = pxsol.core.Requisition(prog, [], bytearray())
    tx = pxsol.core.Transaction.requisition_decode(user.pubkey, [rq])
    tx.message.recent_blockhash = pxsol.base58.decode(pxsol.rpc.get_latest_blockhash({})['blockhash'])
    tx.sign([user.prikey])
    txid = pxsol.rpc.send_transaction(base64.b64encode(tx.serialize()).decode(), {})
    pxsol.rpc.wait([txid])
    r = pxsol.rpc.get_transaction(txid, {})
    for e in r['meta']['logMessages']:
        print(e)


if __name__ == '__main__':
    eval(f'{args.args[0]}()')
