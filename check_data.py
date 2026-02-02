import numpy as np

# Load the face embedding
data = np.load('F:/FYP-120/path_to_your_file.npy', allow_pickle=True)

# View the data
print(f"Shape of data: {data.shape}")
print(data)

# To EDIT: change a value and save
# data[0] = new_value 
# np.save('F:/FYP-120/updated_file.npy', data)