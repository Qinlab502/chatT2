# ![]()chatt2

---

## Introduction


---

## Installation
ChatT2 requires Python 3.8 or later.
```bash
pip install git+https://github.com/Qinlab502/chatT2@master#subdirectory=chatt2
```

## Quickstart
```python
from chatt2 import ChatT2
for i in ChatT2().discussion(
    initial_question="could you describe the biosynthetic pathway formicamycin?", stop_criterion="auto", evaluator_exist=False, cot_mode="auto"
):
    print(i)
```

## Main Parameters

| Parameter       | Type     | Description                                    |
|-----------------|----------|------------------------------------------------|
| `initial_question`| `string` |question from user.                       |
| `max_iterations`| `int` |maximum counts of iteration when cot_mode != disable|
| `stop_criterion`| `Literal["auto", "manual", "convergence"]` |how to stop the iteration when cot_mode != disable |
| `evaluator_exist` | `boolean` |whether evaluator works |
| `cot_mode`|`Literal["disable", "fixed", "updated", "auto"]`|the way of CoT to be changed|



