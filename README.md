# 



<div align="center">
<h2>ProtChat: ChatT2: An Adaptive Framework for Developing an LLM-Based Agent for Bacterial Aromatic Polyketide Research</h2>

![](.\figures\workflow.png)

# 

# Online

We have deployed ChatT2 on this [webpage](https://chatt2.site/#/chat). Any user can access ChatT2's services through a conversational interface. 



# Installation

We recommend users to access our ChatT2 through the online website. Although `data_example` provides sample data, we do not fully disclose our dataset. However, if you have a similar external dataset, you can use ChatT2 as a Python package by following the steps below.

```bash
>>> git clone https://github.com/Qinlab502/chatT2.git
>>> pip install .
```

In the current version, you still need to upload your personal dataset to a third-party database platform and provide an API in the config file.



# User Preference

All user preference settings can be configured in `config.json`. This file will be used for the initialization of ChatT2.

| Parameter       | Type     | Description                                    |
|-----------------|----------|------------------------------------------------|
| `MIN_SCORE_THRESHOLD` | `float` | The minimum threshold value for the relevance of text chunks |
| `TOP_N_CHUNK` | `int` |The number of chunks to keep in the final context |
| `TOP_N_DOCUMENT` | `int` |The number of top relevant documents to keep in the search results |
| `STOP_CRITERION` | `Literal["auto", "manual", "convergence"]` |Defines when the Mentor should stop outputting results |
| `MAX_ITERATION` | `int` |The maximum number of iterative thought cycles for ChatT2|
| `EVALUATOR_EXIST` | `boolean` |Indicates if an evaluator is inputted. If the evaluator is not provided, ChatT2 will provide less precise results. Otherwise, it will yield more accurate results. |
| `COT_MODE` |`Literal["disable", "fixed", "updated", "auto"]`|Defines the method for CoT reasoning|



# Quickstart

Before submitting a question, you need to provide a `config.json` file to initialize ChatT2. After that, you can ask ChatT2 your questions.

```python
import os

os.environ["CONFIG_PATH"] = "config.json"

from chatt2 import ChatT2

# Submit an initial question and iterate over the discussion response
for response in ChatT2.discussion(initial_question="could you describe the biosynthetic pathway formicamycin?"):
    print(response)
```

