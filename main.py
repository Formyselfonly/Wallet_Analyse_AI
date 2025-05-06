# app/main.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
from web3 import Web3
from openai import OpenAI
import os
import dotenv
dotenv.load_dotenv()

# 初始化 Web3 和 OpenAI
INFURA_URL=os.getenv("INFURA_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
client=OpenAI(
    api_key=OPENAI_API_KEY
)

app = FastAPI()

# 示例 ERC20 合约 ABI 片段（这里只需要 balanceOf 方法）
erc20_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

# 示例 ERC721 合约 ABI 片段（NFT）
erc721_abi = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

# 示例合约地址（例如 USDC 和某个 NFT 合约）
usdc_contract = w3.eth.contract(address=w3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"), abi=erc20_abi)
nft_contract = w3.eth.contract(address=w3.to_checksum_address("0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85"), abi=erc721_abi)  # 例如 ENS NFT 合约

class WalletInput(BaseModel):
    address: str

@app.post("/analyze_wallet")
def analyze_wallet(data: WalletInput):
    try:
        address = w3.to_checksum_address(data.address)
        eth_balance = w3.eth.get_balance(address) / 1e18
        usdc_balance = usdc_contract.functions.balanceOf(address).call() / 1e6
        nft_balance = nft_contract.functions.balanceOf(address).call()

        # 构造 prompt 给 OpenAI
        prompt = f"""
        一个以太坊钱包地址如下：{address}
        ETH 余额为：{eth_balance:.4f} ETH
        USDC 余额为：{usdc_balance:.2f} USDC
        NFT 数量为：{nft_balance} 个
        请根据这些信息用中文总结这个用户可能的链上行为特征，并生成简短分析报告。
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        summary=response.choices[0].message.content
        return {
            "summary": summary,
            "eth_balance": eth_balance,
            "usdc_balance": usdc_balance,
            "nft_balance": nft_balance
        }

    except Exception as e:
        return {"error": str(e)}
