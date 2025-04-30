生成数据使用`scrape.py`, 传入需要搜索对象构成的列表, chrome drive的位置, 输出json文件路径

| 接口地址 | 方法 | 描述 |
|:---|:---|:---|
| `/query` | POST | 单轮提问，返回答案 |
| `/chat` | POST | 多轮对话，带记忆 |
| `/keyword_search` | POST | 基于关键词提取进行搜索 |
| `/suggest` | POST | 根据已有食材推荐菜谱 |
| `/similar` | POST | 查找指定菜谱的相似菜谱 |
| `/scale` | POST | 配料按比例缩放 |

参考 `test.ipynb`, 使用时可以把模型从`tinyllama:1.1b`换成大一点的模型