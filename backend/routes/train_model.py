import pandas as pd
from gensim.models import FastText

# Step 1: Load the dataset
df = pd.read_csv("../Skill2Vec_Dataset__Padded_.csv", header=None, engine="python")

# Step 2: Drop the first two columns (job_role and skill_field) → retain only skills
skill_data = df.iloc[:, 2:]

# Step 3: Convert to list of tokenized skill rows, removing NaN/blanks
sentences = [
    [str(s).strip().lower() for s in row if isinstance(s, str) and s.strip()]
    for row in skill_data.values.tolist()
]

# Step 4: Train the FastText model
model = FastText(
    sentences,
    vector_size=100,
    window=5,
    min_count=1,
    sg=1,
    epochs=30,
    workers=4
)

# Step 5: Save the trained vectors
model.wv.save_word2vec_format("trained_skill2vec.txt", binary=False)
