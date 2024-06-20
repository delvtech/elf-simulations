"""A web3.py Contract class for the ERC4626HyperdriveCoreDeployer contract.

DO NOT EDIT.  This file was generated by pypechain.  See documentation at
https://github.com/delvtech/pypechain"""

# contracts have PascalCase names
# pylint: disable=invalid-name

# contracts control how many attributes and arguments we have in generated code
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments

# we don't need else statement if the other conditionals all have return,
# but it's easier to generate
# pylint: disable=no-else-return

# This file is bound to get very long depending on contract sizes.
# pylint: disable=too-many-lines

# methods are overriden with specific arguments instead of generic *args, **kwargs
# pylint: disable=arguments-differ

# consumers have too many opinions on line length
# pylint: disable=line-too-long


from __future__ import annotations

from typing import Any, Type, cast

from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress, HexStr
from typing_extensions import Self
from web3 import Web3
from web3.contract.contract import Contract, ContractConstructor, ContractFunction, ContractFunctions
from web3.exceptions import FallbackNotFound
from web3.types import ABI, BlockIdentifier, CallOverride, TxParams

from .IHyperdriveTypes import Fees, PoolConfig
from .utilities import dataclass_to_tuple, rename_returned_types, try_bytecode_hexbytes

structs = {
    "Fees": Fees,
    "PoolConfig": PoolConfig,
}


class ERC4626HyperdriveCoreDeployerDeployHyperdriveContractFunction(ContractFunction):
    """ContractFunction for the deployHyperdrive method."""

    def __call__(self, name: str, config: PoolConfig, arg3: bytes, target0: str, target1: str, target2: str, target3: str, salt: bytes) -> ERC4626HyperdriveCoreDeployerDeployHyperdriveContractFunction:  # type: ignore
        clone = super().__call__(
            dataclass_to_tuple(name),
            dataclass_to_tuple(config),
            dataclass_to_tuple(arg3),
            dataclass_to_tuple(target0),
            dataclass_to_tuple(target1),
            dataclass_to_tuple(target2),
            dataclass_to_tuple(target3),
            dataclass_to_tuple(salt),
        )
        self.kwargs = clone.kwargs
        self.args = clone.args
        return self

    def call(
        self,
        transaction: TxParams | None = None,
        block_identifier: BlockIdentifier = "latest",
        state_override: CallOverride | None = None,
        ccip_read_enabled: bool | None = None,
    ) -> str:
        """returns str."""
        # Define the expected return types from the smart contract call

        return_types = str

        # Call the function

        raw_values = super().call(transaction, block_identifier, state_override, ccip_read_enabled)
        return cast(str, rename_returned_types(structs, return_types, raw_values))


class ERC4626HyperdriveCoreDeployerContractFunctions(ContractFunctions):
    """ContractFunctions for the ERC4626HyperdriveCoreDeployer contract."""

    deployHyperdrive: ERC4626HyperdriveCoreDeployerDeployHyperdriveContractFunction

    def __init__(
        self,
        abi: ABI,
        w3: "Web3",
        address: ChecksumAddress | None = None,
        decode_tuples: bool | None = False,
    ) -> None:
        super().__init__(abi, w3, address, decode_tuples)
        self.deployHyperdrive = ERC4626HyperdriveCoreDeployerDeployHyperdriveContractFunction.factory(
            "deployHyperdrive",
            w3=w3,
            contract_abi=abi,
            address=address,
            decode_tuples=decode_tuples,
            function_identifier="deployHyperdrive",
        )


erc4626hyperdrivecoredeployer_abi: ABI = cast(
    ABI,
    [
        {
            "type": "function",
            "name": "deployHyperdrive",
            "inputs": [
                {"name": "__name", "type": "string", "internalType": "string"},
                {
                    "name": "_config",
                    "type": "tuple",
                    "internalType": "struct IHyperdrive.PoolConfig",
                    "components": [
                        {"name": "baseToken", "type": "address", "internalType": "contract IERC20"},
                        {"name": "vaultSharesToken", "type": "address", "internalType": "contract IERC20"},
                        {"name": "linkerFactory", "type": "address", "internalType": "address"},
                        {"name": "linkerCodeHash", "type": "bytes32", "internalType": "bytes32"},
                        {"name": "initialVaultSharePrice", "type": "uint256", "internalType": "uint256"},
                        {"name": "minimumShareReserves", "type": "uint256", "internalType": "uint256"},
                        {"name": "minimumTransactionAmount", "type": "uint256", "internalType": "uint256"},
                        {"name": "circuitBreakerDelta", "type": "uint256", "internalType": "uint256"},
                        {"name": "positionDuration", "type": "uint256", "internalType": "uint256"},
                        {"name": "checkpointDuration", "type": "uint256", "internalType": "uint256"},
                        {"name": "timeStretch", "type": "uint256", "internalType": "uint256"},
                        {"name": "governance", "type": "address", "internalType": "address"},
                        {"name": "feeCollector", "type": "address", "internalType": "address"},
                        {"name": "sweepCollector", "type": "address", "internalType": "address"},
                        {"name": "checkpointRewarder", "type": "address", "internalType": "address"},
                        {
                            "name": "fees",
                            "type": "tuple",
                            "internalType": "struct IHyperdrive.Fees",
                            "components": [
                                {"name": "curve", "type": "uint256", "internalType": "uint256"},
                                {"name": "flat", "type": "uint256", "internalType": "uint256"},
                                {"name": "governanceLP", "type": "uint256", "internalType": "uint256"},
                                {"name": "governanceZombie", "type": "uint256", "internalType": "uint256"},
                            ],
                        },
                    ],
                },
                {"name": "", "type": "bytes", "internalType": "bytes"},
                {"name": "_target0", "type": "address", "internalType": "address"},
                {"name": "_target1", "type": "address", "internalType": "address"},
                {"name": "_target2", "type": "address", "internalType": "address"},
                {"name": "_target3", "type": "address", "internalType": "address"},
                {"name": "_salt", "type": "bytes32", "internalType": "bytes32"},
            ],
            "outputs": [{"name": "", "type": "address", "internalType": "address"}],
            "stateMutability": "nonpayable",
        }
    ],
)
# pylint: disable=line-too-long
erc4626hyperdrivecoredeployer_bytecode = HexStr(
    "0x608060405234801561001057600080fd5b506121bf806100206000396000f3fe60806040523480156200001157600080fd5b50600436106200002e5760003560e01c80636a4625791462000033575b600080fd5b6200004a620000443660046200037c565b62000066565b6040516001600160a01b03909116815260200160405180910390f35b604080513360208201529081018290526000908190606001604051602081830303815290604052805190602001208a8a89898989604051620000a890620000e9565b620000b9969594939291906200058d565b8190604051809103906000f5905080158015620000da573d6000803e3d6000fd5b509a9950505050505050505050565b611b4d806200063d83390190565b634e487b7160e01b600052604160045260246000fd5b604051610200810167ffffffffffffffff81118282101715620001345762000134620000f7565b60405290565b600067ffffffffffffffff80841115620001585762000158620000f7565b604051601f8501601f19908116603f01168101908282118183101715620001835762000183620000f7565b816040528093508581528686860111156200019d57600080fd5b858560208301376000602087830101525050509392505050565b80356001600160a01b0381168114620001cf57600080fd5b919050565b600060808284031215620001e757600080fd5b6040516080810181811067ffffffffffffffff821117156200020d576200020d620000f7565b8060405250809150823581526020830135602082015260408301356040820152606083013560608201525092915050565b600061026082840312156200025257600080fd5b6200025c6200010d565b90506200026982620001b7565b81526200027960208301620001b7565b60208201526200028c60408301620001b7565b6040820152606082013560608201526080820135608082015260a082013560a082015260c082013560c082015260e082013560e0820152610100808301358183015250610120808301358183015250610140808301358183015250610160620002f7818401620001b7565b908201526101806200030b838201620001b7565b908201526101a06200031f838201620001b7565b908201526101c062000333838201620001b7565b908201526101e06200034884848301620001d4565b9082015292915050565b600082601f8301126200036457600080fd5b62000375838335602085016200013a565b9392505050565b600080600080600080600080610340898b0312156200039a57600080fd5b883567ffffffffffffffff80821115620003b357600080fd5b818b0191508b601f830112620003c857600080fd5b620003d98c8335602085016200013a565b9950620003ea8c60208d016200023e565b98506102808b01359150808211156200040257600080fd5b50620004118b828c0162000352565b965050620004236102a08a01620001b7565b9450620004346102c08a01620001b7565b9350620004456102e08a01620001b7565b9250620004566103008a01620001b7565b915061032089013590509295985092959890939650565b80516001600160a01b0316825260208101516200049560208401826001600160a01b03169052565b506040810151620004b160408401826001600160a01b03169052565b50606081015160608301526080810151608083015260a081015160a083015260c081015160c083015260e081015160e08301526101008082015181840152506101208082015181840152506101408082015181840152506101608082015162000524828501826001600160a01b03169052565b5050610180818101516001600160a01b03908116918401919091526101a0808301518216908401526101c080830151909116908301526101e090810151805191830191909152602081015161020083015260408101516102208301526060015161024090910152565b600061030080835288518082850152600091505b80821015620005c5576020828b0101516103208386010152602082019150620005a1565b6103209150600082828601015281601f19601f83011685010192505050620005f160208301886200046d565b6001600160a01b0386166102808301526001600160a01b0385166102a08301526001600160a01b0384166102c08301526001600160a01b0383166102e083015297965050505050505056fe6102e06040523480156200001257600080fd5b5060405162001b4d38038062001b4d833981016040819052620000359162000706565b6001600081905585516001600160a01b039081166080908152602080890151831660a0908152918901516101a0908152918901516101c090815260c0808b01516101e090815260e0808d015161020052610120808e0151909352610100808e0151909152610140808e0151909152908c0180515190925281519093015190925281516040908101516101609081529251606090810151610180908152918c01518616610220528b015161024052918a0151600980549186166001600160a01b0319928316179055918a0151600a805491861691841691909117905591890151600b805491851691831691909117905590880151600c80549190931691161790558690869086908690869086906200014d878262000895565b506001600160a01b03938416610260529183166102805282166102a05281166102c052602088015188516200018a94509091169150600162000196565b505050505050620009a3565b604080516001600160a01b038416602482015260448082018490528251808303909101815260649091019091526020810180516001600160e01b0390811663095ea7b360e01b17909152620001f090859083906200026216565b6200025c57604080516001600160a01b038516602482015260006044808301919091528251808303909101815260649091019091526020810180516001600160e01b0390811663095ea7b360e01b17909152620002509186916200031316565b6200025c848262000313565b50505050565b6000806000846001600160a01b03168460405162000281919062000961565b6000604051808303816000865af19150503d8060008114620002c0576040519150601f19603f3d011682016040523d82523d6000602084013e620002c5565b606091505b5091509150818015620002f3575080511580620002f3575080806020019051810190620002f391906200097f565b80156200030a57506000856001600160a01b03163b115b95945050505050565b60006200032a6001600160a01b0384168362000386565b90508051600014158015620003525750808060200190518101906200035091906200097f565b155b156200038157604051635274afe760e01b81526001600160a01b03841660048201526024015b60405180910390fd5b505050565b606062000396838360006200039d565b9392505050565b606081471015620003c45760405163cd78605960e01b815230600482015260240162000378565b600080856001600160a01b03168486604051620003e2919062000961565b60006040518083038185875af1925050503d806000811462000421576040519150601f19603f3d011682016040523d82523d6000602084013e62000426565b606091505b5090925090506200043986838362000443565b9695505050505050565b6060826200045c576200045682620004a7565b62000396565b81511580156200047457506001600160a01b0384163b155b156200049f57604051639996b31560e01b81526001600160a01b038516600482015260240162000378565b508062000396565b805115620004b85780518082602001fd5b604051630a12f52160e11b815260040160405180910390fd5b634e487b7160e01b600052604160045260246000fd5b60405161020081016001600160401b03811182821017156200050d576200050d620004d1565b60405290565b604051601f8201601f191681016001600160401b03811182821017156200053e576200053e620004d1565b604052919050565b60005b838110156200056357818101518382015260200162000549565b50506000910152565b80516001600160a01b03811681146200058457600080fd5b919050565b6000608082840312156200059c57600080fd5b604051608081016001600160401b0381118282101715620005c157620005c1620004d1565b8060405250809150825181526020830151602082015260408301516040820152606083015160608201525092915050565b600061026082840312156200060657600080fd5b62000610620004e7565b90506200061d826200056c565b81526200062d602083016200056c565b602082015262000640604083016200056c565b6040820152606082015160608201526080820151608082015260a082015160a082015260c082015160c082015260e082015160e0820152610100808301518183015250610120808301518183015250610140808301518183015250610160620006ab8184016200056c565b90820152610180620006bf8382016200056c565b908201526101a0620006d38382016200056c565b908201526101c0620006e78382016200056c565b908201526101e0620006fc8484830162000589565b9082015292915050565b60008060008060008061030087890312156200072157600080fd5b86516001600160401b03808211156200073957600080fd5b818901915089601f8301126200074e57600080fd5b815181811115620007635762000763620004d1565b62000778601f8201601f191660200162000513565b91508082528a60208285010111156200079057600080fd5b620007a381602084016020860162000546565b509650620007b790508860208901620005f2565b9450620007c861028088016200056c565b9350620007d96102a088016200056c565b9250620007ea6102c088016200056c565b9150620007fb6102e088016200056c565b90509295509295509295565b600181811c908216806200081c57607f821691505b6020821081036200083d57634e487b7160e01b600052602260045260246000fd5b50919050565b601f8211156200038157600081815260208120601f850160051c810160208610156200086c5750805b601f850160051c820191505b818110156200088d5782815560010162000878565b505050505050565b81516001600160401b03811115620008b157620008b1620004d1565b620008c981620008c2845462000807565b8462000843565b602080601f831160018114620009015760008415620008e85750858301515b600019600386901b1c1916600185901b1785556200088d565b600085815260208120601f198616915b82811015620009325788860151825594840194600190910190840162000911565b5085821015620009515787850151600019600388901b60f8161c191681555b5050505050600190811b01905550565b600082516200097581846020870162000546565b9190910192915050565b6000602082840312156200099257600080fd5b815180151581146200039657600080fd5b60805160a05160c05160e05161010051610120516101405161016051610180516101a0516101c0516101e05161020051610220516102405161026051610280516102a0516102c05161108f62000abe6000396000818161057c0152818161063c015281816107350152818161076501526107c3015260008181610535015261095e0152600081816105d001526106d20152600081816101e4015281816103a60152818161060c0152818161066e015281816106a00152818161070601528181610798015281816107f40152818161092c0152610991015260005050600050506000505060005050600050506000505060005050600050506000505060005050600050506000505060005050600050506000505061108f6000f3fe6080604052600436106101cd5760003560e01c80639cd241af116100f7578063cbc1343411610095578063e44808bc11610064578063e44808bc1461059e578063e4af29d1146102dd578063eac3e799146105be578063f698da25146105f2576101cd565b8063cbc134341461031a578063d899e1121461056a578063dbbe807014610557578063ded06231146103e0576101cd565b8063a5107626116100d1578063a5107626146102dd578063a6e8a85914610523578063ab033ea9146102dd578063cba2e58d14610557576101cd565b80639cd241af14610503578063a22cb465146104b0578063a42dce80146102dd576101cd565b806330adf81f1161016f5780634ed2d6ac1161013e5780634ed2d6ac146104955780637180c8ca146104b057806377d05ff4146104d05780639032c726146104e3576101cd565b806330adf81f1461040e5780633e691db914610442578063414f826d146104625780634c2ac1d914610482576101cd565b806317fad7fc116101ab57806317fad7fc146103545780631c0f12b61461037457806321b57d531461039457806329b23fc1146103e0576101cd565b806301681a62146102dd57806302329a29146102ff578063074a6de91461031a575b3480156101d957600080fd5b5060003660606000807f00000000000000000000000000000000000000000000000000000000000000006001600160a01b0316858560405161021c929190610a67565b600060405180830381855af49150503d8060008114610257576040519150601f19603f3d011682016040523d82523d6000602084013e61025c565b606091505b5091509150811561028057604051638bb0a34b60e01b815260040160405180910390fd5b600061028b82610a77565b90506001600160e01b03198116636e64089360e11b146102ad57815160208301fd5b8151600319810160048401908152926102ce91810160200190602401610ae8565b80519650602001945050505050f35b3480156102e957600080fd5b506102fd6102f8366004610bad565b610607565b005b34801561030b57600080fd5b506102fd6102f8366004610be6565b34801561032657600080fd5b5061033a610335366004610c13565b610634565b604080519283526020830191909152015b60405180910390f35b34801561036057600080fd5b506102fd61036f366004610caf565b610669565b34801561038057600080fd5b506102fd61038f366004610d44565b61069b565b3480156103a057600080fd5b506103c87f000000000000000000000000000000000000000000000000000000000000000081565b6040516001600160a01b03909116815260200161034b565b3480156103ec57600080fd5b506104006103fb366004610d8c565b6106cb565b60405190815260200161034b565b34801561041a57600080fd5b506104007f65619c8664d6db8aae8c236ad19598696159942a4245b23b45565cc18e97367381565b34801561044e57600080fd5b5061040061045d366004610de6565b6106ff565b34801561046e57600080fd5b506102fd61047d366004610e23565b610730565b610400610490366004610e45565b61075e565b3480156104a157600080fd5b506102fd61038f366004610ea9565b3480156104bc57600080fd5b506102fd6104cb366004610ef3565b610793565b6104006104de366004610c13565b6107bc565b3480156104ef57600080fd5b506102fd6104fe366004610f28565b6107ef565b34801561050f57600080fd5b506102fd61051e366004610fa6565b610927565b34801561052f57600080fd5b506103c87f000000000000000000000000000000000000000000000000000000000000000081565b61033a610565366004610d8c565b610956565b34801561057657600080fd5b506103c87f000000000000000000000000000000000000000000000000000000000000000081565b3480156105aa57600080fd5b506102fd6105b9366004610fde565b61098c565b3480156105ca57600080fd5b506103c87f000000000000000000000000000000000000000000000000000000000000000081565b3480156105fe57600080fd5b506104006109bd565b6106307f0000000000000000000000000000000000000000000000000000000000000000610a4b565b5050565b6000806106607f0000000000000000000000000000000000000000000000000000000000000000610a4b565b50935093915050565b6106927f0000000000000000000000000000000000000000000000000000000000000000610a4b565b50505050505050565b6106c47f0000000000000000000000000000000000000000000000000000000000000000610a4b565b5050505050565b60006106f67f0000000000000000000000000000000000000000000000000000000000000000610a4b565b50949350505050565b600061072a7f0000000000000000000000000000000000000000000000000000000000000000610a4b565b50919050565b6107597f0000000000000000000000000000000000000000000000000000000000000000610a4b565b505050565b60006107897f0000000000000000000000000000000000000000000000000000000000000000610a4b565b5095945050505050565b6107597f0000000000000000000000000000000000000000000000000000000000000000610a4b565b60006107e77f0000000000000000000000000000000000000000000000000000000000000000610a4b565b509392505050565b6000807f00000000000000000000000000000000000000000000000000000000000000006001600160a01b03166108246109bd565b60405160248101919091527f65619c8664d6db8aae8c236ad19598696159942a4245b23b45565cc18e97367360448201526001600160a01b03808c1660648301528a16608482015288151560a482015260c4810188905260ff871660e4820152610104810186905261012481018590526101440160408051601f198184030181529181526020820180516001600160e01b03166314e5f07b60e01b179052516108cd919061103d565b600060405180830381855af49150503d8060008114610908576040519150601f19603f3d011682016040523d82523d6000602084013e61090d565b606091505b50915091508161091f57805160208201fd5b805160208201f35b6109507f0000000000000000000000000000000000000000000000000000000000000000610a4b565b50505050565b6000806109827f0000000000000000000000000000000000000000000000000000000000000000610a4b565b5094509492505050565b6109b57f0000000000000000000000000000000000000000000000000000000000000000610a4b565b505050505050565b60408051808201825260018152603160f81b60209182015281517f2aef22f9d7df5f9d21c56d14029233f3fdaa91917727e1eb68e504d27072d6cd818301527fc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc681840152466060820152306080808301919091528351808303909101815260a0909101909252815191012090565b6060600080836001600160a01b03166000366040516108cd9291905b8183823760009101908152919050565b805160208201516001600160e01b03198082169291906004831015610aa65780818460040360031b1b83161693505b505050919050565b634e487b7160e01b600052604160045260246000fd5b60005b83811015610adf578181015183820152602001610ac7565b50506000910152565b600060208284031215610afa57600080fd5b815167ffffffffffffffff80821115610b1257600080fd5b818401915084601f830112610b2657600080fd5b815181811115610b3857610b38610aae565b604051601f8201601f19908116603f01168101908382118183101715610b6057610b60610aae565b81604052828152876020848701011115610b7957600080fd5b610b8a836020830160208801610ac4565b979650505050505050565b6001600160a01b0381168114610baa57600080fd5b50565b600060208284031215610bbf57600080fd5b8135610bca81610b95565b9392505050565b80358015158114610be157600080fd5b919050565b600060208284031215610bf857600080fd5b610bca82610bd1565b60006060828403121561072a57600080fd5b600080600060608486031215610c2857600080fd5b8335925060208401359150604084013567ffffffffffffffff811115610c4d57600080fd5b610c5986828701610c01565b9150509250925092565b60008083601f840112610c7557600080fd5b50813567ffffffffffffffff811115610c8d57600080fd5b6020830191508360208260051b8501011115610ca857600080fd5b9250929050565b60008060008060008060808789031215610cc857600080fd5b8635610cd381610b95565b95506020870135610ce381610b95565b9450604087013567ffffffffffffffff80821115610d0057600080fd5b610d0c8a838b01610c63565b90965094506060890135915080821115610d2557600080fd5b50610d3289828a01610c63565b979a9699509497509295939492505050565b60008060008060808587031215610d5a57600080fd5b843593506020850135610d6c81610b95565b92506040850135610d7c81610b95565b9396929550929360600135925050565b60008060008060808587031215610da257600080fd5b843593506020850135925060408501359150606085013567ffffffffffffffff811115610dce57600080fd5b610dda87828801610c01565b91505092959194509250565b600060208284031215610df857600080fd5b813567ffffffffffffffff811115610e0f57600080fd5b610e1b84828501610c01565b949350505050565b60008060408385031215610e3657600080fd5b50508035926020909101359150565b600080600080600060a08688031215610e5d57600080fd5b85359450602086013593506040860135925060608601359150608086013567ffffffffffffffff811115610e9057600080fd5b610e9c88828901610c01565b9150509295509295909350565b60008060008060808587031215610ebf57600080fd5b843593506020850135610ed181610b95565b9250604085013591506060850135610ee881610b95565b939692955090935050565b60008060408385031215610f0657600080fd5b8235610f1181610b95565b9150610f1f60208401610bd1565b90509250929050565b600080600080600080600060e0888a031215610f4357600080fd5b8735610f4e81610b95565b96506020880135610f5e81610b95565b9550610f6c60408901610bd1565b945060608801359350608088013560ff81168114610f8957600080fd5b9699959850939692959460a0840135945060c09093013592915050565b600080600060608486031215610fbb57600080fd5b833592506020840135610fcd81610b95565b929592945050506040919091013590565b600080600080600060a08688031215610ff657600080fd5b85359450602086013561100881610b95565b9350604086013561101881610b95565b925060608601359150608086013561102f81610b95565b809150509295509295909350565b6000825161104f818460208701610ac4565b919091019291505056fea26469706673582212207dc0d3048eb9fa39647fcb18b21f05a366a8662970518b0f42ad8dd3c038b7d264736f6c63430008140033a26469706673582212204e3bd70a346efccc18b4b660b272ea6b7260a63a4d1df34706653a65a4da9f2d64736f6c63430008140033"
)


class ERC4626HyperdriveCoreDeployerContract(Contract):
    """A web3.py Contract class for the ERC4626HyperdriveCoreDeployer contract."""

    abi: ABI = erc4626hyperdrivecoredeployer_abi
    bytecode: bytes | None = try_bytecode_hexbytes(
        erc4626hyperdrivecoredeployer_bytecode, "erc4626hyperdrivecoredeployer"
    )

    def __init__(self, address: ChecksumAddress | None = None) -> None:
        try:
            # Initialize parent Contract class
            super().__init__(address=address)
            self.functions = ERC4626HyperdriveCoreDeployerContractFunctions(erc4626hyperdrivecoredeployer_abi, self.w3, address)  # type: ignore

        except FallbackNotFound:
            print("Fallback function not found. Continuing...")

    functions: ERC4626HyperdriveCoreDeployerContractFunctions

    @classmethod
    def constructor(cls) -> ContractConstructor:  # type: ignore
        """Creates a transaction with the contract's constructor function.

        Parameters
        ----------

        w3 : Web3
            A web3 instance.
        account : LocalAccount
            The account to use to deploy the contract.

        Returns
        -------
        Self
            A deployed instance of the contract.

        """

        return super().constructor()

    @classmethod
    def deploy(cls, w3: Web3, account: LocalAccount | ChecksumAddress) -> Self:
        """Deploys and instance of the contract.

        Parameters
        ----------
        w3 : Web3
            A web3 instance.
        account : LocalAccount
            The account to use to deploy the contract.

        Returns
        -------
        Self
            A deployed instance of the contract.
        """
        deployer = cls.factory(w3=w3)
        constructor_fn = deployer.constructor()

        # if an address is supplied, try to use a web3 default account
        if isinstance(account, str):
            tx_hash = constructor_fn.transact({"from": account})
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            deployed_contract = deployer(address=tx_receipt.contractAddress)  # type: ignore
            return deployed_contract

        # otherwise use the account provided.
        deployment_tx = constructor_fn.build_transaction()
        current_nonce = w3.eth.get_transaction_count(account.address, "pending")
        deployment_tx.update({"nonce": current_nonce})

        # Sign the transaction with local account private key
        signed_tx = account.sign_transaction(deployment_tx)

        # Send the signed transaction and wait for receipt
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        deployed_contract = deployer(address=tx_receipt.contractAddress)  # type: ignore
        return deployed_contract

    @classmethod
    def factory(cls, w3: Web3, class_name: str | None = None, **kwargs: Any) -> Type[Self]:
        """Deploys and instance of the contract.

        Parameters
        ----------
        w3 : Web3
            A web3 instance.
        class_name: str | None
            The instance class name.

        Returns
        -------
        Self
            A deployed instance of the contract.
        """
        contract = super().factory(w3, class_name, **kwargs)
        contract.functions = ERC4626HyperdriveCoreDeployerContractFunctions(erc4626hyperdrivecoredeployer_abi, w3, None)

        return contract
