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
        请根据这些信息用中文总结这个用户可能的链上行为特征，并生成分析报告。
        以下是一个分析报告案例:------
        ## 🔍 行为特征分析
        ### 1. 资产配置
        该钱包持有一定数量的
        ETH和USDC，表明用户可能参与了以太坊生态系统中的活动。
        ### 2. 稳定币持有
        USDC的持有量显示用户可能关注资产的稳定性，可能用于交易、储值或参与
        DeFi协议。
        ### 3. NFT 参与度
        持有NFT
        表明用户可能参与了NFT市场，可能是收藏者、投资者或参与了相关的去中心化应用。
        ## 📈 活跃度评估
        根据资产的分布和种类，用户显示出对以太坊生态系统的多方面兴趣，可能在
        DeFi、NFT或其他领域有一定的参与度。
        ## 🧠 用户画像推测
        综合上述信息，用户可能是：
        - 对加密资产有一定了解的投资者
        - 积极参与以太坊生态系统的用户
        - 对数字收藏品和新兴技术感兴趣的个体
        ------
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
