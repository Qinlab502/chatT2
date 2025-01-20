import copy
import json
import subprocess
import time
from io import StringIO
from tempfile import NamedTemporaryFile
from typing import Literal

import pandas as pd
import requests
from pymsaviz import MsaViz

from ..data import (
    dynamic_images_cache_path,
    fasta_nucleotide_text,
    fasta_protein_text,
    structure_database_file,
)
from .retrieve_structured_data import search_structured_database
from ...template import function_calling_system_prompt, function_calling_template
from ...utils import (
    dict_to_markdown_table,
    get_text_completion,
    get_text_completion_with_tools,
    get_text_completion_with_stream,
)
from ...agents.base_agent import BaseAgent


class FunctionMaster(BaseAgent):
    def __init__(self, query, fasta_file_name=None):
        self.function_list = function_calling_template
        self.system_prompt = function_calling_system_prompt
        self.function_calling_api = get_text_completion_with_tools

        self.query = query
        self.fasta_file_name = fasta_file_name

    def loop(self):
        # self.main_messages.messages.append({"role": "user", "content": self.query})
        if self.fasta_file_name:
            with open(self.fasta_file_name) as handle:  # noqa: PTH123
                fasta = handle.read()
                self.query += "\nthe content in the fasta file is" + fasta
        self.tools_messages = []
        self.tools_messages.insert(0, {"role": "system", "content": self.system_prompt})
        self.tools_messages.append({"role": "user", "content": self.query})

        response = self.function_calling_api(self.tools_messages, tools=self.function_list)
        if response.finish_reason == "tool_calls":
            conversation_about_tool_call = []
            print(response.message.tool_calls)
            for tool_call in response.message.tool_calls:
                if (
                    tool_call.function.name == "gene_function_annotation"
                ):  # 关于并行函数调用的部分是yield返回，理论上来说正常情况下，当上面两个函数被调用时，真正的工具函数是不需要被调用额
                    fasta_text = json.loads(tool_call.function.arguments)["fasta_text"]
                    type_ = json.loads(tool_call.function.arguments)["type"]
                    # result = self._gene_function_annotation(fasta_text, type_, self.fasta_file_name)
                    result = self._gene_function_annotation(fasta_text, type_, None)

                    conversation_about_tool_call.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "gene_function_annotation",
                        "content": json.dumps({"annotation_result": dict_to_markdown_table(result)}),
                    })
                elif tool_call.function.name == "ask_for_clarification":
                    clarification_question = json.loads(tool_call.function.arguments)["clarification_question"]
                    conversation_about_tool_call.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "ask_for_clarification",
                        "content": self.input_from_user(clarification_question),
                    })
                elif tool_call.function.name == "multiple_sequence_alignment":
                    fasta_text = json.loads(tool_call.function.arguments)["fasta_text"]
                    # msa_result, msa_vis_url = self._multiple_sequence_alignment(fasta_text, self.fasta_file_name)
                    msa_result, msa_vis_url = self._multiple_sequence_alignment(fasta_text, None)
                    conversation_about_tool_call.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "multiple_sequence_alignment",
                        "content": json.dumps({
                            "msa_result": msa_result,
                            "msa_result_visualization_url": msa_vis_url,
                        }),
                    })
                elif tool_call.function.name == "pubchem":
                    compound_name = json.loads(tool_call.function.arguments)["compound_name"]
                    compound_information = self._pubchem(compound_name)
                    conversation_about_tool_call.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "pubchem",
                        "content": json.dumps({"compound_information": compound_information}),
                    })

                else:
                    assert ValueError("function name in funcation calling error")
            conversation_about_tool_call = [
                response.message,
                *conversation_about_tool_call,
            ]
            # print(conversation_about_tool_call)
            self.tools_messages += conversation_about_tool_call
            return self.output_from_llm(self.tools_messages)

        else:
            print(response.finish_reason)
            return ""

    def _pubchem(self, compoundname):
        compoundname = "Accramycin"
        query = {
            "select": "*",
            "collection": "compound",
            "order": ["relevancescore,desc"],
            "start": 0,
            "limit": 10000,
            "where": {"ands": [{"*": compoundname}]},
            "width": 1000000,
            "listids": 0,
        }
        url = "https://pubchem.ncbi.nlm.nih.gov/sdq/sdqagent.cgi?infmt=json&outfmt=json&query=" + json.dumps(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
        }
        response = requests.get(url, headers=headers)
        result = json.loads(response.text)
        try:
            return json.dumps(result["SDQOutputSet"][0]["rows"][0])
        except IndexError:
            return "Information about the compound is missing, please check the the compoundname"

    def ask_for_clarification(self):
        self.input_from_user("Please clarify your question")

    def _multiple_sequence_alignment(self, fasta_text, fasta_file_name=None):
        # 这里fasta_file是指当fasta_file存在时，fasta_text中会包含fasta_file的前2行的内容，当fasta_file存在时，直接执行fasta_file的指令，不考虑输入框和文件都包含fasta序列情况
        if not fasta_file_name:
            with NamedTemporaryFile(mode="w+", encoding="utf-8") as fasta_file, NamedTemporaryFile(mode="w+", encoding="utf-8") as msa_file:
                fasta_file.write(fasta_text)
                fasta_file.seek(0)
                cmd = ["mafft", "--auto", fasta_file.name]  # 这个指令是打印到标准输出
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
                msa_file.write(result.stdout)
                msa_file.seek(0)
                mv = MsaViz(
                    msa_file.name,
                    color_scheme="Taylor",
                    wrap_length=80,
                    show_grid=True,
                    show_consensus=True,
                )
                current_timestamp = int(time.time())
                msa_vis_url = dynamic_images_cache_path + f"{current_timestamp}_msa_vis.jpg"

                mv.savefig(msa_vis_url)
        return result.stdout, msa_vis_url

    def _gene_function_annotation(self, fasta_text, type_: Literal["dna", "protein"], fasta_file_name=None):
        if not fasta_file_name:
            with NamedTemporaryFile(mode="w+", encoding="utf-8", suffix=".fasta") as fasta_file, NamedTemporaryFile(
                mode="w+", encoding="utf-8", suffix=".txt"
            ) as annotation_result_file:
                fasta_file.write(fasta_text)
                fasta_file.seek(0)
                if type_ == "dna":
                    target_fasta_file = fasta_nucleotide_text
                elif type_ == "protein":
                    target_fasta_file = fasta_protein_text
                else:
                    assert ValueError("gene_function_annotation_type efrror")
                cmd = [
                    "mmseqs",
                    "easy-search",
                    fasta_file.name,
                    target_fasta_file,
                    annotation_result_file.name,
                    "tmp",
                ]
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )  # noqa: F841
                with open(annotation_result_file.name) as f:  # noqa: PTH123
                    annotation_result = f.read()
                    print(annotation_result)

        columns = [
            "Query Sequence ID",
            "Target Sequence ID",
            "Sequence Identity",
            "Alignment Length",
            "Mismatches",
            "Gap Openings",
            "Query Start",
            "Query End",
            "Target Start",
            "Target End",
            "E-value",
            "Bit Score",
        ]
        data_io = StringIO(annotation_result)
        print(annotation_result)
        df_annotation_result = pd.read_csv(data_io, delim_whitespace=True, header=None, names=columns)
        annotation_result = df_annotation_result.loc[
            :,
            [
                "Query Sequence ID",
                "Target Sequence ID",
                "Alignment Length",
                "Sequence Identity",
                "Bit Score",
            ],
        ]
        annotation_result = annotation_result.sort_values(by="Sequence Identity", ascending=False).iloc[:5]

        mibig_number_list = []
        for target_sequence_id in annotation_result["Target Sequence ID"]:
            mibig_number_list.append(target_sequence_id.split("|")[0])

        sql = "select * from gene where " + " ".join([f"mibig_number = {i!r} or" for i in list(set(mibig_number_list))])[:-3]

        print(sql)
        gene_table = search_structured_database(structure_database_file, sql)
        annotation = []
        for target_sequence_id in annotation_result["Target Sequence ID"]:
            mibig_number, gene_name = target_sequence_id.split("|")
            annotation.append(
                gene_table[(gene_table["mibig_number"] == mibig_number) & (gene_table["gene_name"] == gene_name)]["gene_protein_product"]
            )
        annotation_result["annotation"] = annotation

        return annotation_result
