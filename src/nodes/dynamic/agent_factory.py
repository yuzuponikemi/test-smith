"""
Dynamic Agent Factory - ノードを設定から動的生成

使用例:
    factory = AgentFactory()
    analyzer = factory.create_node("analyzer", {
        "model": "llama3",
        "prompt_template": "...",
        "output_key": "analyzed_data"
    })
"""

from typing import Any, Callable

from langchain_core.prompts import PromptTemplate

from src.models import get_model_by_name


class AgentFactory:
    """ノードを設定から動的生成するファクトリー"""

    def __init__(self):
        self.node_templates = {
            "analyzer": self._create_analyzer_template,
            "synthesizer": self._create_synthesizer_template,
            "evaluator": self._create_evaluator_template,
            "planner": self._create_planner_template,
        }

    def create_node(self, node_type: str, config: dict[str, Any]) -> Callable:
        """
        設定に基づいてノード関数を動的生成

        Args:
            node_type: ノードタイプ ("analyzer", "synthesizer"など)
            config: ノード設定
                - model: LLMモデル名
                - prompt_template: プロンプトテンプレート文字列
                - input_keys: ステートから取得するキーのリスト
                - output_key: 結果を保存するステートキー
                - system_message: システムメッセージ（オプション）

        Returns:
            LangGraphノード関数
        """
        if node_type not in self.node_templates:
            raise ValueError(f"Unknown node type: {node_type}")

        template_func = self.node_templates[node_type]
        return template_func(config)

    def _create_analyzer_template(self, config: dict) -> Callable:
        """汎用分析ノードを生成"""

        def analyzer_node(state: dict) -> dict:
            # 入力データを収集
            inputs = {}
            for key in config.get("input_keys", []):
                inputs[key] = state.get(key, "")

            # プロンプトを構築
            prompt_template = PromptTemplate.from_template(config["prompt_template"])
            prompt = prompt_template.format(**inputs)

            # LLMを実行
            model = get_model_by_name(config.get("model", "llama3"))
            if config.get("structured_output"):
                model = model.with_structured_output(config["structured_output"])

            result = model.invoke(prompt)

            # 結果を返す
            output_key = config.get("output_key", "result")
            return {output_key: result}

        return analyzer_node

    def _create_synthesizer_template(self, config: dict) -> Callable:
        """汎用統合ノードを生成"""

        def synthesizer_node(state: dict) -> dict:
            inputs = {}
            for key in config.get("input_keys", []):
                value = state.get(key, [])
                # リストを結合
                if isinstance(value, list):
                    inputs[key] = "\n\n".join(str(item) for item in value)
                else:
                    inputs[key] = str(value)

            prompt_template = PromptTemplate.from_template(config["prompt_template"])
            prompt = prompt_template.format(**inputs)

            model = get_model_by_name(config.get("model", "command-r"))
            result = model.invoke(prompt)

            output_key = config.get("output_key", "report")
            return {output_key: result.content if hasattr(result, "content") else str(result)}

        return synthesizer_node

    def _create_evaluator_template(self, config: dict) -> Callable:
        """汎用評価ノードを生成"""

        def evaluator_node(state: dict) -> dict:
            inputs = {}
            for key in config.get("input_keys", []):
                inputs[key] = state.get(key, "")

            prompt_template = PromptTemplate.from_template(config["prompt_template"])
            prompt = prompt_template.format(**inputs)

            model = get_model_by_name(config.get("model", "command-r"))
            if config.get("structured_output"):
                model = model.with_structured_output(config["structured_output"])

            result = model.invoke(prompt)

            output_key = config.get("output_key", "evaluation")
            return {output_key: result}

        return evaluator_node

    def _create_planner_template(self, config: dict) -> Callable:
        """汎用計画ノードを生成"""

        def planner_node(state: dict) -> dict:
            inputs = {}
            for key in config.get("input_keys", []):
                inputs[key] = state.get(key, "")

            prompt_template = PromptTemplate.from_template(config["prompt_template"])
            prompt = prompt_template.format(**inputs)

            model = get_model_by_name(config.get("model", "llama3"))

            # Structured outputが必須（計画は構造化データ）
            if not config.get("structured_output"):
                raise ValueError("Planner nodes require structured_output schema")

            model = model.with_structured_output(config["structured_output"])
            result = model.invoke(prompt)

            # 結果を辞書として展開
            return result.model_dump() if hasattr(result, "model_dump") else dict(result)

        return planner_node


# 使用例: YAML設定からワークフローを生成
"""
# workflow_config.yaml
nodes:
  - name: strategic_planner
    type: planner
    config:
      model: llama3
      prompt_template: |
        Given query: {query}
        Create a strategic plan...
      input_keys: [query]
      structured_output: StrategicPlan

  - name: result_analyzer
    type: analyzer
    config:
      model: command-r
      prompt_template: |
        Analyze these results: {search_results}
      input_keys: [search_results]
      output_key: analyzed_data
"""
