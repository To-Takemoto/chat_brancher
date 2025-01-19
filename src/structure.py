import structlog
from anytree import AnyNode, importer, exporter, find

from .llm_client import LLMClient
from .models import User, TreeStructure, Message

from peewee import DoesNotExist

logger = structlog.get_logger()

class TreeStructureHandler:
    """
    ここで扱うtreeは明示されていなければエンコードされたものとしている．
    """
    def __init__(self, owner: User) -> None:
        self.owner = owner
        self.tree = None
        self.selected_node = None
        self.tree_id = None
        self._init_flag = False

    def init_structure(self) -> None:
        response = TreeStructure.create(owner = self.owner, structure = {})
        self.tree_id = response.id
        self._init_flag = True#これを利用することで，メッセージが一切ない状態を判定する．

    def load_structure(self, chat_id: int) -> None:
        if self._chat_is_ownded(chat_id):
            self.tree_id = chat_id

        tree = self._load_tree(self.tree_id)
        if tree:
            self.tree = tree
        else:
            self.tree = None
            self._init_flag = True
            #↑self.tree=Noneの場合，何もメッセージがないということなので，initと同等の状態．

    def _chat_is_ownded(self, chat_id: int) -> bool:
        "self.ownerが本当にそのchatを所有しているのかを量る"
        owns = list(TreeStructure.select().where(TreeStructure.owner == self.owner))
        owns_id = [int(tree.id) for tree in owns]
        if chat_id in owns_id:
            return True
        else:
            try:
                if TreeStructure.get_by_id(chat_id):
                    print(f"owner;{self.owner.id} does not have chat which has provided chat id")
                    print("hint: 渡されたidを持つチャットはあるが，それがUserのものではないようだ．")
            except DoesNotExist:
                print(f"NOT found chat has provided id;{chat_id} in DB")
            raise DoesNotExist

    def _load_tree(self, tree_id) -> AnyNode | None:
        tree_dict = TreeStructure.get_by_id(tree_id).structure
        tree = importer.JsonImporter().import_(tree_dict)

        def not_null_validate(target_tree: AnyNode):
            try:
                target_tree.message_id
                return True
            except AttributeError:
                return False

        if not_null_validate(tree):
            return tree
        else:
            return None

    def select_node(self, message_id: int) -> None:
        if self._message_is_owned(message_id):
            self.selected_node:AnyNode = find(self.tree, filter_=lambda node: node.message_id == message_id)
        

    def _message_is_owned(self, message_id: int) -> bool:
        tree_messages = list(Message.select().where(Message.chat == self.tree_id))
        tree_messages_id = [int(message.id) for message in tree_messages]
        if message_id in tree_messages_id:
            return True
        else:
            try:
                Message.get_by_id(message_id)
                print("メッセージはあるけど，このツリーには所属していないようだ．")
            except DoesNotExist:
                print("そもそも，そのpkを持つメッセージは存在しない．")
            raise DoesNotExist

    def update_tree(self, message_id: int) -> None:
        new_node = AnyNode(message_id = message_id, parent = self.selected_node)
        #↑当たり前だけど，selected_nodeがself.treeに含まれていることを前提としている．
        if self._init_flag:
            self.tree = new_node
            self._init_flag = False
        self.selected_node = new_node
        new_tree_data = str(exporter.JsonExporter().export(self.tree))
        response = TreeStructure.update(structure = new_tree_data).execute()

    def load_selected_node_path(self) -> list[dict, dict]:
        path = self.selected_node.path
        encoded_path = [int(node.message_id) for node in path]
        decoded_path = self.decode_tree(encoded_path)
        return decoded_path

    def decode_tree(self, message_id_list: list[int, int]) -> list[dict, dict]:
        decoded_history = []
        for message_id in message_id_list:
            message_model:Message = Message.select().where(Message.id == message_id)
            content = {"role":message_model.role, "content":message_model.content}
            content | {"id":message_id}
            decoded_history.append(content)
        return decoded_history


test_user = User.get_by_id(1)
tree_structure_handle = TreeStructureHandler(test_user)
tree_structure_handle.init_structure()
tree_structure_handle.load_structure(2)


decoded_history1 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "こんにちは、元気ですか？"},
    {"role": "assistant", "content": "こんにちは！元気です。お手伝いできることがあれば教えてください。"},
    {"role": "user", "content": "AIについて詳しく教えてください。"},
    {"role": "assistant", "content": "AI（人工知能）は、人間の知的行動を模倣するように設計された技術のことです。例えば、機械学習や自然言語処理などがあります。具体的にどの分野について知りたいですか？"},
    {"role": "user", "content": "機械学習について詳しく知りたいです。"},
    {"role": "assistant", "content": "機械学習は、データから学習し予測や判断を行う技術です。アルゴリズムとしては、教師あり学習、教師なし学習、強化学習などがあります。具体的な質問があれば教えてください！"}
]

encoded_history1 = [
    {"role": "system", "content": "1"},
    {"role": "user", "content": "2"},
    {"role": "assistant", "content": "3"},
    {"role": "user", "content": "4"},
    {"role": "assistant", "content": "5"},
    {"role": "user", "content": "6"},
    {"role": "assistant", "content": "7"}
]

# chat_history2 = [
#     {"role": "system", "content": "You are an expert project manager assistant."},
#     {"role": "user", "content": "プロジェクトの進捗が遅れています。どうすれば良いですか？"},
#     {"role": "assistant", "content": "まず、遅れの原因を特定することが重要です。具体的には、リソース不足、タスクの見積もりミス、優先順位の問題などが考えられます。原因はわかっていますか？"},
#     {"role": "user", "content": "タスクの見積もりが甘かったと思います。"},
#     {"role": "assistant", "content": "見積もりが原因の場合、以下のアクションを検討してください:\n1. タスクを小さな単位に分解して再見積もりする。\n2. チームと協力して現実的なスケジュールを作成する。\n3. 優先度の低いタスクを後回しにする。\nどれから始めますか？"},
#     {"role": "user", "content": "タスクの再見積もりから始めます。"},
#     {"role": "assistant", "content": "いいですね。チームメンバーを集め、タスクごとの所要時間を再確認しましょう。また、過去のデータを参照すると精度が上がります。他にサポートが必要ですか？"}
# ]

# encoded_history2 = [
#     {"role": "system", "content": "8"},
#     {"role": "user", "content": "9"},
#     {"role": "assistant", "content": "10"},
#     {"role": "user", "content": "11"},
#     {"role": "assistant", "content": "12"},
#     {"role": "user", "content": "13"},
#     {"role": "assistant", "content": "14"}
# ]