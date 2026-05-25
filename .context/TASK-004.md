**MUST** 创建目录 `.context/.done/`

```python
import os

os.makedirs(os.path.join(os.getcwd(), ".context", ".done"), exist_ok=True)
```
