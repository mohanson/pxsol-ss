import argparse
import base64
import json
import pxsol
import subprocess
import os

parser = argparse.ArgumentParser()
parser.add_argument('--net', type=str, choices=['develop', 'mainnet', 'testnet'], default='develop')
parser.add_argument('--prikey', type=str, default=None)
parser.add_argument('--generate-key', action='store_true', help='生成新的密钥对')
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
    os.makedirs('res', exist_ok=True)
    try:
        with open('res/info.json', 'r') as f:
            info = json.load(f)
    except FileNotFoundError:
        info = {}
    info[k] = v
    with open('res/info.json', 'w') as f:
        json.dump(info, f, indent=4)


def info_load(k: str) -> str:
    with open('res/info.json', 'r') as f:
        info = json.load(f)
    return info[k]


def get_prikey():
    """获取私钥，优先级：命令行参数 > 配置文件 > 生成新密钥"""
    if args.prikey:
        return args.prikey
    
    # 尝试从配置文件读取
    try:
        saved_prikey = info_load('prikey')
        print(f"使用已保存的私钥")
        return saved_prikey
    except (FileNotFoundError, KeyError):
        pass
    
    # 生成新密钥
    print("未找到私钥，正在生成新密钥...")
    prikey = pxsol.core.PriKey.random()
    pubkey = prikey.pubkey()
    prikey_b58 = prikey.base58()
    
    print(f"新私钥: {prikey_b58}")
    print(f"新地址: {pubkey.base58()}")
    
    # 保存私钥到配置
    info_save('prikey', prikey_b58)
    print("私钥已保存到 res/info.json")
    
    # 尝试自动转账（仅在开发网络）
    if args.net == 'develop':
        print("\n正在自动转账 SOL...")
        try:
            # 使用 solana-cli 从默认钱包转账
            addr = pubkey.base58()
            result = subprocess.run(
                f'solana transfer {addr} 50 --url http://127.0.0.1:8899 --allow-unfunded-recipient',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"成功转账 50 SOL 到新地址")
                # 验证余额
                balance = pxsol.rpc.get_balance(addr, {})
                print(f"当前余额: {balance / 10**9} SOL")
            else:
                print("自动转账失败，请手动转账：")
                print(f"solana transfer {addr} 50 --url http://127.0.0.1:8899 --allow-unfunded-recipient")
        except Exception as e:
            print(f"自动转账失败: {e}")
            print("请手动转账：")
            print(f"solana transfer {pubkey.base58()} 50 --url http://127.0.0.1:8899 --allow-unfunded-recipient")
    
    return prikey_b58


def generate_key():
    """生成新密钥并保存"""
    prikey = pxsol.core.PriKey.random()
    pubkey = prikey.pubkey()
    prikey_b58 = prikey.base58()
    
    print(f"新私钥: {prikey_b58}")
    print(f"新地址: {pubkey.base58()}")
    
    # 保存私钥
    info_save('prikey', prikey_b58)
    print("\n私钥已保存到 res/info.json")
    
    # 在开发网络提示转账
    if args.net == 'develop':
        print("\n请执行以下命令转账：")
        print(f"solana transfer {pubkey.base58()} 50 --url http://127.0.0.1:8899 --allow-unfunded-recipient")


def deploy():
    """部署程序"""
    prikey_str = get_prikey()
    user = pxsol.wallet.Wallet(pxsol.core.PriKey.base58_decode(prikey_str))
    
    # 检查余额
    balance = pxsol.rpc.get_balance(user.pubkey.base58(), {})
    print(f"账户余额: {balance / 10**9} SOL")
    if balance < 10 * 10**9:  # 少于 10 SOL
        print("警告: 余额可能不足以部署程序")
    
    call('cargo build-sbf -- -Znext-lockfile-bump')
    pxsol.log.debugln(f'main: deploy program')
    with open('target/deploy/solana_storage.so', 'rb') as f:
        data = bytearray(f.read())
    prog_pubkey = user.program_deploy(data)
    pxsol.log.debugln(f'main: deploy program pubkey={prog_pubkey}')
    info_save('pubkey', prog_pubkey.base58())


def update():
    """更新程序"""
    prikey_str = get_prikey()
    user = pxsol.wallet.Wallet(pxsol.core.PriKey.base58_decode(prikey_str))
    prog_pubkey = pxsol.core.PubKey(pxsol.base58.decode(info_load('pubkey')))
    call('cargo build-sbf -- -Znext-lockfile-bump')
    pxsol.log.debugln(f'main: update program')
    with open('target/deploy/solana_storage.so', 'rb') as f:
        data = bytearray(f.read())
    user.program_update(prog_pubkey, data)


def save():
    """保存数据"""
    prikey_str = get_prikey()
    user = pxsol.wallet.Wallet(pxsol.core.PriKey.base58_decode(prikey_str))
    prog_pubkey = pxsol.core.PubKey.base58_decode(info_load('pubkey'))
    data_pubkey = prog_pubkey.derive_pda(user.pubkey.p)
    rq = pxsol.core.Requisition(prog_pubkey, [], bytearray())
    rq.account.append(pxsol.core.AccountMeta(user.pubkey, 3))
    rq.account.append(pxsol.core.AccountMeta(data_pubkey, 1))
    rq.account.append(pxsol.core.AccountMeta(pxsol.program.System.pubkey, 0))
    rq.account.append(pxsol.core.AccountMeta(pxsol.program.SysvarRent.pubkey, 0))
    rq.data = bytearray(args.args[1].encode())
    tx = pxsol.core.Transaction.requisition_decode(user.pubkey, [rq])
    tx.message.recent_blockhash = pxsol.base58.decode(pxsol.rpc.get_latest_blockhash({})['blockhash'])
    tx.sign([user.prikey])
    txid = pxsol.rpc.send_transaction(base64.b64encode(tx.serialize()).decode(), {})
    pxsol.rpc.wait([txid])
    r = pxsol.rpc.get_transaction(txid, {})
    for e in r['meta']['logMessages']:
        print(e)


def load():
    """读取数据"""
    prikey_str = get_prikey()
    user = pxsol.wallet.Wallet(pxsol.core.PriKey.base58_decode(prikey_str))
    prog_pubkey = pxsol.core.PubKey.base58_decode(info_load('pubkey'))
    data_pubkey = prog_pubkey.derive_pda(user.pubkey.p)
    info = pxsol.rpc.get_account_info(data_pubkey.base58(), {})
    print(base64.b64decode(info['data'][0]).decode())


def show_info():
    """显示当前配置信息"""
    try:
        prikey_str = info_load('prikey')
        user = pxsol.wallet.Wallet(pxsol.core.PriKey.base58_decode(prikey_str))
        print(f"私钥: {prikey_str}")
        print(f"地址: {user.pubkey.base58()}")
        
        balance = pxsol.rpc.get_balance(user.pubkey.base58(), {})
        print(f"余额: {balance / 10**9} SOL")
        
        try:
            prog_pubkey = info_load('pubkey')
            print(f"程序地址: {prog_pubkey}")
        except KeyError:
            print("程序地址: 未部署")
    except (FileNotFoundError, KeyError):
        print("未找到配置信息")


if __name__ == '__main__':
    # 处理 --generate-key 参数
    if args.generate_key:
        generate_key()
    else:
        # 执行命令
        command = args.args[0]
        if command == 'info':
            show_info()
        else:
            eval(f'{command}()')