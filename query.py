from pathlib import Path
import pandas as pd
from utils.embedding import get_embedding
from utils.code_parser import extract_functions_from_repo

root_dir = Path.home()
print(root_dir)
code_root = root_dir /'Desktop'/ 'codequery'/'test'

print(code_root)
# Extract all functions from the repository
all_funcs = extract_functions_from_repo(code_root)


df = pd.DataFrame(all_funcs)
print(df)
df['code_embedding'] = df['code'].apply(lambda x: get_embedding(x, model='text-embedding-3-small'))
df['filepath'] = df['filepath'].map(lambda x: Path(x).relative_to(code_root))
df.to_csv("data/code_search_openai-python.csv", index=False)
df.head()